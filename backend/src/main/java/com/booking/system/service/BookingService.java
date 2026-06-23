package com.booking.system.service;

import com.booking.system.config.RoomosRedisLockProperties;
import com.booking.system.entity.Booking;
import com.booking.system.entity.Property;
import com.booking.system.entity.Room;
import com.booking.system.entity.RoomType;
import com.booking.system.messaging.BookingMessagePublisher;
import com.booking.system.mapper.BookingRepository;
import com.booking.system.mapper.RoomRepository;
import com.booking.system.mapper.RoomTypeRepository;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.EnumSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
public class BookingService {

    private static final Set<Booking.BookingStatus> INVENTORY_STATUSES = EnumSet.of(
            Booking.BookingStatus.PENDING,
            Booking.BookingStatus.CONFIRMED,
            Booking.BookingStatus.CHECKED_IN
    );

    @Autowired
    private BookingRepository bookingRepository;

    @Autowired
    private RoomTypeRepository roomTypeRepository;

    @Autowired
    private RoomRepository roomRepository;

    @Autowired
    private RedissonClient redissonClient;

    @Autowired
    private RoomosRedisLockProperties redisLockProperties;

    @Autowired
    private PropertyCacheService propertyCacheService;

    @Autowired
    private BookingMessagePublisher bookingMessagePublisher;

    public List<Booking> getAllBookings() {
        return bookingRepository.findAll();
    }

    public Optional<Booking> getBookingById(Long id) {
        return bookingRepository.findById(id);
    }

    public Optional<Booking> getBookingByNumber(String bookingNumber) {
        return bookingRepository.findByBookingNumber(bookingNumber);
    }

    public List<Booking> getBookingsByUserId(Long userId) {
        return bookingRepository.findByUser_Id(userId);
    }

    public List<Booking> getBookingsByPropertyId(Long propertyId) {
        return bookingRepository.findByProperty_Id(propertyId);
    }

    public List<Booking> getBookingsByMerchantId(Long merchantId) {
        return bookingRepository.findByProperty_MerchantId(merchantId);
    }

    public List<Booking> getBookingsByStatus(String status) {
        return bookingRepository.findByStatus(Booking.BookingStatus.valueOf(status));
    }

    @Transactional
    public Booking createBooking(Booking booking) {
        RoomType roomType = prepareBookingForSave(booking);
        // 创建分布式锁及相应的事务处理
        Booking saved = saveBookingWithInventoryGuard(booking, roomType, null);
        // 清空redis热点数据缓存
        propertyCacheService.clearTopProperties();
        // 创建消息队列
        publishBookingCreatedAfterCommit(saved);
        return saved;
    }

    @Transactional
    public Booking updateBooking(Long id, Booking booking) {
        Booking existing = bookingRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Booking not found"));
        booking.setId(id);
        booking.setBookingNumber(existing.getBookingNumber());
        booking.setCreatedAt(existing.getCreatedAt());
        RoomType roomType = prepareBookingForSave(booking);
        Booking saved = saveBookingWithInventoryGuard(booking, roomType, id);
        propertyCacheService.clearTopProperties();
        return saved;
    }

    @Transactional
    public void deleteBooking(Long id) {
        bookingRepository.deleteById(id);
        propertyCacheService.clearTopProperties();
    }

    @Transactional
    public Booking cancelBooking(Long id, String reason) {
        Booking booking = bookingRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Booking not found"));
        booking.setStatus(Booking.BookingStatus.CANCELLED);
        booking.setPaymentStatus(Booking.PaymentStatus.UNPAID);
        booking.setCancellationReason(reason);
        booking.setCancellationTime(LocalDateTime.now());
        booking.setUpdatedAt(LocalDateTime.now());
        Booking saved = bookingRepository.save(booking);
        propertyCacheService.clearTopProperties();
        publishBookingCancelledAfterCommit(saved, false);
        return saved;
    }

    @Transactional
    public Booking checkIn(Long id) {
        Booking booking = bookingRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Booking not found"));

        if (booking.getStatus() == Booking.BookingStatus.CANCELLED || booking.getStatus() == Booking.BookingStatus.REFUNDED) {
            throw new IllegalStateException("Cannot check in a cancelled or refunded booking");
        }
        Booking.PaymentStatus paymentStatus = booking.getPaymentStatus();
        if (paymentStatus == null || paymentStatus == Booking.PaymentStatus.UNPAID) {
            throw new IllegalStateException("Booking has not been paid");
        }
        if (booking.getStatus() == Booking.BookingStatus.CHECKED_IN) {
            return booking;
        }
        booking.setStatus(Booking.BookingStatus.CHECKED_IN);
        booking.setCheckInTime(LocalDateTime.now());
        booking.setUpdatedAt(LocalDateTime.now());
        Booking saved = bookingRepository.save(booking);
        propertyCacheService.clearTopProperties();
        return saved;
    }

    @Transactional
    public Booking checkOut(Long id) {
        Booking booking = bookingRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Booking not found"));

        if (booking.getStatus() == Booking.BookingStatus.CANCELLED || booking.getStatus() == Booking.BookingStatus.REFUNDED) {
            throw new IllegalStateException("Cannot check out a cancelled or refunded booking");
        }
        Booking.PaymentStatus paymentStatus = booking.getPaymentStatus();
        if (paymentStatus == null || paymentStatus == Booking.PaymentStatus.UNPAID) {
            throw new IllegalStateException("Booking has not been paid");
        }
        if (booking.getStatus() != Booking.BookingStatus.CHECKED_IN) {
            throw new IllegalStateException("Booking must be checked in before checkout");
        }
        booking.setStatus(Booking.BookingStatus.CHECKED_OUT);
        booking.setCheckOutTime(LocalDateTime.now());
        booking.setUpdatedAt(LocalDateTime.now());
        Booking saved = bookingRepository.save(booking);
        propertyCacheService.clearTopProperties();
        return saved;
    }

    @Transactional
    public void autoCancelUnpaidBooking(Long bookingId) {
        Booking booking = bookingRepository.findById(bookingId)
                .orElseThrow(() -> new RuntimeException("Booking not found"));

        if (booking.getStatus() == Booking.BookingStatus.CANCELLED
                || booking.getStatus() == Booking.BookingStatus.REFUNDED
                || booking.getStatus() == Booking.BookingStatus.CHECKED_OUT) {
            return;
        }
        if (booking.getPaymentStatus() != null && booking.getPaymentStatus() != Booking.PaymentStatus.UNPAID) {
            return;
        }

        booking.setStatus(Booking.BookingStatus.CANCELLED);
        booking.setCancellationReason("15分钟未支付，系统自动取消");
        booking.setCancellationTime(LocalDateTime.now());
        booking.setUpdatedAt(LocalDateTime.now());
        Booking saved = bookingRepository.save(booking);
        propertyCacheService.clearTopProperties();
        publishBookingCancelledAfterCommit(saved, true);
    }

    private String generateBookingNumber() {
        return "BK" + System.currentTimeMillis() + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    private RoomType prepareBookingForSave(Booking booking) {
        if (booking.getRoomType() == null || booking.getRoomType().getId() == null) {
            throw new IllegalStateException("roomTypeId 不能为空");
        }

        RoomType roomType = roomTypeRepository.findById(booking.getRoomType().getId())
                .orElseThrow(() -> new RuntimeException("Room type not found"));

        if (roomType.getStatus() != RoomType.RoomTypeStatus.ACTIVE) {
            throw new IllegalStateException("当前房型不可预订");
        }

        Property property = roomType.getProperty();
        if (property == null) {
            throw new IllegalStateException("当前房型未关联民宿");
        }
        if (booking.getProperty() != null
                && booking.getProperty().getId() != null
                && !booking.getProperty().getId().equals(property.getId())) {
            throw new IllegalStateException("房型与民宿不匹配");
        }

        booking.setRoomType(roomType);
        booking.setProperty(property);

        if (booking.getRoom() != null && booking.getRoom().getId() != null) {
            Room room = roomRepository.findByIdAndRoomType_Id(booking.getRoom().getId(), roomType.getId())
                    .orElseThrow(() -> new IllegalStateException("房间不存在或不属于当前房型"));
            if (room.getStatus() != Room.RoomStatus.AVAILABLE) {
                throw new IllegalStateException("当前房间不可预订");
            }
            booking.setRoom(room);
        }

        applyDefaults(booking, roomType);
        return roomType;
    }

    private Booking saveBookingWithInventoryGuard(Booking booking, RoomType roomType, Long excludeBookingId) {
        if (!occupiesInventory(booking.getStatus())) {
            return bookingRepository.save(booking);
        }

        RLock lock = redissonClient.getLock("booking:roomType:" + roomType.getId());
        tryAcquireLock(lock);
        try {
            registerUnlockAfterTransaction(lock);
            validateAvailability(booking, roomType, excludeBookingId);
            return bookingRepository.save(booking);
        } finally {
            if (!TransactionSynchronizationManager.isActualTransactionActive() && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }

    private boolean tryAcquireLock(RLock lock) {
        try {
            boolean locked = lock.tryLock(
                    resolveWaitMillis(redisLockProperties.getWaitTime(), 3000),
                    resolveLeaseMillis(redisLockProperties.getLeaseTime(), 10000),
                    TimeUnit.MILLISECONDS
            );
            if (!locked) {
                throw new IllegalStateException("当前房型预订繁忙，请稍后重试");
            }
            return true;
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("获取预订锁被中断", ex);
        }
    }

    private void registerUnlockAfterTransaction(RLock lock) {
        if (!TransactionSynchronizationManager.isActualTransactionActive()) {
            throw new IllegalStateException("Inventory lock requires an active transaction");
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCompletion(int status) {
                if (lock.isHeldByCurrentThread()) {
                    lock.unlock();
                }
            }
        });
    }

    private void validateAvailability(Booking booking, RoomType roomType, Long excludeBookingId) {
        long totalAvailableRooms = roomRepository.countByRoomType_IdAndStatus(roomType.getId(), Room.RoomStatus.AVAILABLE);
        long conflictingBookings = bookingRepository.countConflictingBookings(
                roomType.getId(),
                booking.getCheckInDate(),
                booking.getCheckOutDate(),
                INVENTORY_STATUSES,
                excludeBookingId
        );

        if (booking.getRoom() != null && booking.getRoom().getId() != null) {
            long conflictingRoomBookings = bookingRepository.countConflictingBookingsByRoomId(
                    booking.getRoom().getId(),
                    booking.getCheckInDate(),
                    booking.getCheckOutDate(),
                    INVENTORY_STATUSES,
                    excludeBookingId
            );
            if (conflictingRoomBookings > 0) {
                throw new IllegalStateException("当前房间在所选日期已被预订");
            }
        }

        if (totalAvailableRooms <= 0 || conflictingBookings >= totalAvailableRooms) {
            throw new IllegalStateException("当前房型在所选日期已满房");
        }
    }

    private boolean occupiesInventory(Booking.BookingStatus status) {
        return status != null && INVENTORY_STATUSES.contains(status);
    }

    private void applyDefaults(Booking booking, RoomType roomType) {
        if (booking.getBookingNumber() == null) {
            booking.setBookingNumber(generateBookingNumber());
        }

        validateBookingDates(booking);

        long nights = ChronoUnit.DAYS.between(booking.getCheckInDate(), booking.getCheckOutDate());
        booking.setNights((int) Math.max(nights, 1));

        if (booking.getBasePrice() == null && roomType != null) {
            booking.setBasePrice(roomType.getBasePrice());
        }

        BigDecimal basePrice = booking.getBasePrice() != null ? booking.getBasePrice() : BigDecimal.ZERO;
        BigDecimal discount = booking.getDiscountAmount() != null ? booking.getDiscountAmount() : BigDecimal.ZERO;
        BigDecimal couponDiscount = booking.getCouponDiscount() != null ? booking.getCouponDiscount() : BigDecimal.ZERO;
        BigDecimal serviceFee = booking.getServiceFee() != null ? booking.getServiceFee() : BigDecimal.ZERO;
        int nightCount = booking.getNights() != null ? booking.getNights() : 1;
        BigDecimal total = basePrice.multiply(BigDecimal.valueOf(nightCount))
                .add(serviceFee)
                .subtract(discount)
                .subtract(couponDiscount);
        booking.setTotalAmount(total.max(BigDecimal.ZERO));

        if (booking.getStatus() == null) {
            booking.setStatus(Booking.BookingStatus.PENDING);
        }
        if (booking.getPaymentStatus() == null) {
            booking.setPaymentStatus(Booking.PaymentStatus.UNPAID);
        }
        if (booking.getCreatedAt() == null) {
            booking.setCreatedAt(LocalDateTime.now());
        }
        booking.setUpdatedAt(LocalDateTime.now());
    }

    private void validateBookingDates(Booking booking) {
        if (booking.getCheckInDate() == null || booking.getCheckOutDate() == null) {
            throw new IllegalStateException("入住和离店日期不能为空");
        }
        if (!booking.getCheckOutDate().isAfter(booking.getCheckInDate())) {
            throw new IllegalStateException("离店日期必须晚于入住日期");
        }
    }

    private long resolveWaitMillis(Duration duration, long fallback) {
        if (duration == null || duration.isZero()) {
            return fallback;
        }
        return duration.toMillis();
    }

    private long resolveLeaseMillis(Duration duration, long fallback) {
        if (duration == null || duration.isZero()) {
            return fallback;
        }
        if (duration.isNegative()) {
            return -1L;
        }
        return duration.toMillis();
    }

    private void publishBookingCreatedAfterCommit(Booking booking) {
        if (!TransactionSynchronizationManager.isActualTransactionActive()) {
            bookingMessagePublisher.publishBookingCreated(booking);
            bookingMessagePublisher.publishBookingAutoCancel(booking);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                bookingMessagePublisher.publishBookingCreated(booking);
                bookingMessagePublisher.publishBookingAutoCancel(booking);
            }
        });
    }

    private void publishBookingCancelledAfterCommit(Booking booking, boolean autoCancelled) {
        if (!TransactionSynchronizationManager.isActualTransactionActive()) {
            bookingMessagePublisher.publishBookingCancelled(booking, autoCancelled);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                bookingMessagePublisher.publishBookingCancelled(booking, autoCancelled);
            }
        });
    }
}

