-- =====================================================
-- Sample Data for WebApp E-commerce Database
-- Dữ liệu mẫu cho hệ thống bán hàng
-- =====================================================

-- Clear existing data (use with caution!)
-- TRUNCATE TABLE chitietdonhang CASCADE;
-- TRUNCATE TABLE donhang CASCADE;
-- TRUNCATE TABLE chitietgiohang CASCADE;
-- TRUNCATE TABLE giohang CASCADE;
-- TRUNCATE TABLE xuatkhochitiet CASCADE;
-- TRUNCATE TABLE yeucauxuatkho CASCADE;
-- TRUNCATE TABLE nhapkhochitiet CASCADE;
-- TRUNCATE TABLE yeucaunhapkho CASCADE;
-- TRUNCATE TABLE hangtonkho CASCADE;
-- TRUNCATE TABLE phanbocungcap CASCADE;
-- TRUNCATE TABLE cuahang CASCADE;
-- TRUNCATE TABLE kho CASCADE;
-- TRUNCATE TABLE danhgiacuahang CASCADE;
-- TRUNCATE TABLE danhgia CASCADE;
-- TRUNCATE TABLE sanpham CASCADE;
-- TRUNCATE TABLE danhmuc CASCADE;
-- TRUNCATE TABLE nhanvien CASCADE;

-- =====================================================
-- 1. DANH MỤC (CATEGORIES)
-- =====================================================

INSERT INTO danhmuc (madm, tendm) VALUES
    ('DM001', 'Điện Tử & Thiết Bị Công Nghệ'),
    ('DM002', 'Gia Dụng & Nội Thất'),
    ('DM003', 'Thực Phẩm & Đồ Uống'),
    ('DM004', 'Quần Áo & Giày Dép'),
    ('DM005', 'Sách & Văn Phòng Phẩm'),
    ('DM006', 'Mỹ Phẩm & Chăm Sóc'),
    ('DM007', 'Thiết Bị Thể Thao'),
    ('DM008', 'Mẹ & Bé'),
    ('DM009', 'Đồ Chơi & Giải Trí'),
    ('DM010', 'Vật Dụng Gia Đình')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 2. SẢN PHẨM (PRODUCTS)
-- =====================================================

INSERT INTO sanpham (masp, ten, danhmuc, gia, trangthai) VALUES
    -- Điện Tử
    ('SP001', 'iPhone 15 Pro Max', 'DM001', 30000000, 'Đang bán'),
    ('SP002', 'Samsung Galaxy S24', 'DM001', 22000000, 'Đang bán'),
    ('SP003', 'iPad Air 2024', 'DM001', 18000000, 'Đang bán'),
    ('SP004', 'MacBook Pro 16"', 'DM001', 65000000, 'Đang bán'),
    ('SP005', 'Dell XPS 15', 'DM001', 45000000, 'Đang bán'),
    ('SP006', 'Sony WH-1000XM5 Headphones', 'DM001', 8000000, 'Đang bán'),
    ('SP007', 'Samsung TV 55" QLED', 'DM001', 18000000, 'Đang bán'),
    
    -- Gia Dụng
    ('SP101', 'Nồi cơm điện thông minh', 'DM002', 1500000, 'Đang bán'),
    ('SP102', 'Máy lạnh Daikin', 'DM002', 8000000, 'Đang bán'),
    ('SP103', 'Tủ lạnh LG', 'DM002', 12000000, 'Đang bán'),
    ('SP104', 'Máy rửa chén Bosch', 'DM002', 18000000, 'Đang bán'),
    ('SP105', 'Bộ chăn ga gối cao cấp', 'DM002', 1200000, 'Đang bán'),
    
    -- Thực Phẩm
    ('SP201', 'Gạo Bắc Thơm', 'DM003', 120000, 'Đang bán'),
    ('SP202', 'Dầu ăn Premium', 'DM003', 80000, 'Đang bán'),
    ('SP203', 'Nước Cam Tươi', 'DM003', 35000, 'Đang bán'),
    ('SP204', 'Cà Phê Nguyên Chất', 'DM003', 150000, 'Đang bán'),
    ('SP205', 'Mật Ong Rừng', 'DM003', 200000, 'Đang bán'),
    
    -- Quần Áo
    ('SP301', 'Áo Thun Nam Cotton', 'DM004', 150000, 'Đang bán'),
    ('SP302', 'Quần Jean Nam', 'DM004', 400000, 'Đang bán'),
    ('SP303', 'Váy Nữ Thanh Lịch', 'DM004', 450000, 'Đang bán'),
    ('SP304', 'Giày Sneaker Nike', 'DM004', 1200000, 'Đang bán'),
    
    -- Sách
    ('SP401', 'Lập Trình Python Cơ Bản', 'DM005', 250000, 'Đang bán'),
    ('SP402', 'Tư Duy Chiến Lược', 'DM005', 180000, 'Đang bán'),
    
    -- Mỹ Phẩm
    ('SP501', 'Kem Dưỡng Da Mặt', 'DM006', 320000, 'Đang bán'),
    ('SP502', 'Dầu Gội Dầu Dừa', 'DM006', 120000, 'Đang bán'),
    
    -- Thể Thao
    ('SP601', 'Vợt Cầu Lông Wilson', 'DM007', 800000, 'Đang bán'),
    ('SP602', 'Xe Đạp Địa Hình', 'DM007', 5000000, 'Đang bán'),
    
    -- Mẹ & Bé
    ('SP701', 'Sữa Bột Cho Bé', 'DM008', 450000, 'Đang bán'),
    ('SP702', 'Bộ Đồ Chơi Cho Bé', 'DM008', 250000, 'Đang bán'),
    
    -- Đồ Chơi
    ('SP801', 'Lego Classic', 'DM009', 600000, 'Đang bán'),
    ('SP802', 'Xe Điều Khiển Từ Xa', 'DM009', 350000, 'Đang bán'),
    
    -- Vật Dụng
    ('SP901', 'Bàn Chải Bạn', 'DM010', 45000, 'Đang bán'),
    ('SP902', 'Đèn LED Thông Minh', 'DM010', 250000, 'Đang bán')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 3. NHÂN VIÊN (EMPLOYEES)
-- =====================================================

INSERT INTO nhanvien (manv, ten, email, sdt, matkhau, role) VALUES
    ('NV001', 'Nguyễn Văn Admin', 'admin@webapp.com', '0901234567', 'hashed_admin_pwd', 'Admin'),
    ('NV002', 'Lê Thị Kế Toán', 'ketoan@webapp.com', '0902345678', 'hashed_kt_pwd', 'Kế Toán'),
    ('NV003', 'Trần Văn Hùng', 'hung@webapp.com', '0903456789', 'hashed_nv_pwd', 'Nhân Viên'),
    ('NV004', 'Phạm Thị Hoa', 'hoa@webapp.com', '0904567890', 'hashed_nv_pwd', 'Nhân Viên'),
    ('NV005', 'Vũ Đình Minh', 'minh@webapp.com', '0905678901', 'hashed_user_pwd', 'User')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 4. KHO HÀNG (WAREHOUSES)
-- =====================================================

INSERT INTO kho (makho, ten, loai, diachi, geom) VALUES
    ('KHO001', 'Kho Tổng Hà Nội', 'Kho Tổng', 
     '123 Đường Tây Sơn, Phường Việt Tân, Quận Đống Đa, Hà Nội, 100000', 
     ST_GeomFromText('POINT(105.8137 21.0285)', 4326)),
    
    ('KHO002', 'Kho Chi Nhánh TP.HCM', 'Kho Chi Nhánh', 
     '456 Nguyễn Hữu Cảnh, Phường 22, Quận Bình Thạnh, TP.HCM, 700000', 
     ST_GeomFromText('POINT(106.7223 10.8020)', 4326)),
    
    ('KHO003', 'Kho Chi Nhánh Đà Nẵng', 'Kho Chi Nhánh', 
     '789 Đường Ngô Mây, Quận Hải Châu, Đà Nẵng, 550000', 
     ST_GeomFromText('POINT(107.0682 16.0356)', 4326)),
    
    ('KHO004', 'Kho Lạnh - Hà Nội', 'Kho Tổng', 
     '321 Đường Hoàng Quốc Việt, Quận Cầu Giấy, Hà Nội, 100000', 
     ST_GeomFromText('POINT(105.7870 21.0277)', 4326))
ON CONFLICT DO NOTHING;

-- =====================================================
-- 5. CỬA HÀNG (STORES)
-- =====================================================

INSERT INTO cuahang (mach, ten, loai, diachi, sdt, trangthai, geom, giomocua, giodongcua) VALUES
    ('CH001', 'Cửa Hàng Tiện Lợi Hà Nội 1', 'Tiện Lợi', 
     '789 Đường Ngô Thì Nhậm, Quận Hai Bà Trưng, Hà Nội', '(024) 3812-1234', 'Hoạt động', 
     ST_GeomFromText('POINT(105.8445 21.0016)', 4326), '06:00:00'::time, '22:00:00'::time),
    
    ('CH002', 'Cửa Hàng Điện Tử TP.HCM 1', 'Điện Tử', 
     '101 Pasteur, Phường Bến Nghé, Quận 1, TP.HCM', '(028) 3821-5678', 'Hoạt động', 
     ST_GeomFromText('POINT(106.6955 10.7813)', 4326), '09:00:00'::time, '21:00:00'::time),
    
    ('CH003', 'Cửa Hàng Gia Dụng Hà Nội', 'Gia Dụng', 
     '555 Đường Lý Thái Tổ, Quận Hoàn Kiếm, Hà Nội', '(024) 3933-6789', 'Hoạt động', 
     ST_GeomFromText('POINT(105.8520 21.0127)', 4326), '08:00:00'::time, '20:00:00'::time),
    
    ('CH004', 'Cửa Hàng Thực Phẩm Đà Nẵng', 'Tiện Lợi', 
     '999 Đường Nguyễn Tất Thành, Quận Hải Châu, Đà Nẵng', '(0236) 3821-234', 'Hoạt động', 
     ST_GeomFromText('POINT(107.0682 16.0267)', 4326), '07:00:00'::time, '21:00:00'::time),
    
    ('CH005', 'Cửa Hàng Quần Áo TP.HCM', 'Gia Dụng', 
     '222 Đường Đồng Khởi, Quận 1, TP.HCM', '(028) 3829-9999', 'Hoạt động', 
     ST_GeomFromText('POINT(106.6996 10.7756)', 4326), '10:00:00'::time, '20:00:00'::time)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 6. HÀNG TỒN KHO (INVENTORY)
-- =====================================================

INSERT INTO hangtonkho (makho, masp, soluong) VALUES
    -- Kho Hà Nội - Tồn kho nhiều
    ('KHO001', 'SP001', 50),
    ('KHO001', 'SP002', 45),
    ('KHO001', 'SP003', 30),
    ('KHO001', 'SP101', 100),
    ('KHO001', 'SP102', 15),
    ('KHO001', 'SP201', 500),
    ('KHO001', 'SP202', 300),
    ('KHO001', 'SP301', 200),
    ('KHO001', 'SP302', 100),
    ('KHO001', 'SP501', 80),
    ('KHO001', 'SP601', 25),
    ('KHO001', 'SP701', 60),
    ('KHO001', 'SP801', 40),
    ('KHO001', 'SP901', 150),
    
    -- Kho TP.HCM
    ('KHO002', 'SP001', 35),
    ('KHO002', 'SP004', 20),
    ('KHO002', 'SP005', 10),
    ('KHO002', 'SP103', 8),
    ('KHO002', 'SP203', 250),
    ('KHO002', 'SP204', 180),
    ('KHO002', 'SP303', 120),
    ('KHO002', 'SP304', 45),
    ('KHO002', 'SP401', 70),
    ('KHO002', 'SP502', 95),
    ('KHO002', 'SP602', 12),
    
    -- Kho Đà Nẵng
    ('KHO003', 'SP002', 25),
    ('KHO003', 'SP003', 18),
    ('KHO003', 'SP101', 50),
    ('KHO003', 'SP201', 200),
    ('KHO003', 'SP301', 100),
    ('KHO003', 'SP701', 35),
    
    -- Kho Lạnh
    ('KHO004', 'SP102', 200),
    ('KHO004', 'SP103', 150),
    ('KHO004', 'SP203', 400)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 7. PHÂN BỔ CUNG CẤP (SUPPLY DISTRIBUTION)
-- =====================================================

INSERT INTO phanbocungcap (mach, makho, uu_tien) VALUES
    -- Cửa hàng 1 ưu tiên từ kho 1 trước
    ('CH001', 'KHO001', 1),
    ('CH001', 'KHO003', 2),
    ('CH001', 'KHO004', 3),
    
    -- Cửa hàng 2 ưu tiên từ kho 2 trước
    ('CH002', 'KHO002', 1),
    ('CH002', 'KHO004', 2),
    
    -- Cửa hàng 3 ưu tiên từ kho 1 trước
    ('CH003', 'KHO001', 1),
    ('CH003', 'KHO004', 2),
    
    -- Cửa hàng 4 ưu tiên từ kho 3 trước
    ('CH004', 'KHO003', 1),
    ('CH004', 'KHO001', 2),
    
    -- Cửa hàng 5 ưu tiên từ kho 2 trước
    ('CH005', 'KHO002', 1),
    ('CH005', 'KHO004', 2)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 8. YÊU CẦU NHẬP KHO (STOCK IN)
-- =====================================================

INSERT INTO yeucaunhapkho (mayc, ngay, trangthai, manv) VALUES
    ('YC001', '2024-04-01', 'Đã duyệt', 'NV001'),
    ('YC002', '2024-04-05', 'Đã duyệt', 'NV002'),
    ('YC003', '2024-04-10', 'Chờ duyệt', 'NV003'),
    ('YC004', '2024-04-15', 'Đã duyệt', 'NV001'),
    ('YC005', '2024-04-20', 'Đã duyệt', 'NV004')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 9. NHẬP KHO CHI TIẾT (STOCK IN DETAILS)
-- =====================================================

INSERT INTO nhapkhochitiet (mayc, makho, masp, soluong) VALUES
    ('YC001', 'KHO001', 'SP001', 50),
    ('YC001', 'KHO001', 'SP002', 45),
    ('YC001', 'KHO001', 'SP003', 30),
    ('YC002', 'KHO001', 'SP101', 100),
    ('YC002', 'KHO001', 'SP102', 15),
    ('YC003', 'KHO002', 'SP001', 35),
    ('YC003', 'KHO002', 'SP004', 20),
    ('YC004', 'KHO001', 'SP201', 500),
    ('YC004', 'KHO001', 'SP202', 300),
    ('YC005', 'KHO003', 'SP002', 25)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 10. ĐÁNH GIÁ SẢN PHẨM (PRODUCT RATINGS)
-- =====================================================

INSERT INTO danhgia (masp, nguoidung, diem, binhluan) VALUES
    ('SP001', 'Khách hàng 1', 5, 'Sản phẩm chất lượng, giao hàng nhanh'),
    ('SP001', 'Khách hàng 2', 4, 'Tốt nhưng giá hơi cao'),
    ('SP002', 'Khách hàng 3', 5, 'Rất hài lòng'),
    ('SP101', 'Khách hàng 4', 4, 'Tốt, tiêu điện không quá'),
    ('SP201', 'Khách hàng 5', 5, 'Gạo ngon, giá rẻ'),
    ('SP301', 'Khách hàng 6', 3, 'Bình thường'),
    ('SP501', 'Khách hàng 7', 5, 'Sản phẩm rất tốt cho da'),
    ('SP601', 'Khách hàng 8', 4, 'Chất lượng ổn định')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 11. ĐÁNH GIÁ CỬA HÀNG (STORE RATINGS)
-- =====================================================

INSERT INTO danhgiacuahang (mach, nguoidung, diem, binhluan) VALUES
    ('CH001', 'Khách hàng 1', 5, 'Cửa hàng sạch sẽ, nhân viên thân thiện'),
    ('CH001', 'Khách hàng 2', 4, 'Hàng hóa đa dạng'),
    ('CH002', 'Khách hàng 3', 5, 'Sản phẩm điện tử chính hãng'),
    ('CH003', 'Khách hàng 4', 4, 'Giá cạnh tranh'),
    ('CH005', 'Khách hàng 5', 5, 'Quần áo đẹp, giá tốt')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 12. GIỎ HÀNG VÀ CHI TIẾT (SHOPPING CART)
-- =====================================================

INSERT INTO giohang (manv, session_id) VALUES
    ('NV005', 'session_001'),
    (NULL, 'session_guest_001'),
    (NULL, 'session_guest_002')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 13. ĐƠN HÀNG (ORDERS)
-- =====================================================

INSERT INTO donhang (madh, manv, tennguoinhan, sdt_nhan, diachi_nhan, trangthai, phuongthuctt) VALUES
    ('DH001', 'NV003', 'Trần Văn A', '0912345678', '123 Đường ABC, Hà Nội', 'Đã hoàn thành', 'COD'),
    ('DH002', 'NV003', 'Nguyễn Thị B', '0987654321', '456 Đường XYZ, TP.HCM', 'Đang giao', 'MoMo'),
    ('DH003', 'NV004', 'Phạm Văn C', '0923456789', '789 Đường DEF, Đà Nẵng', 'Đang xử lý', 'COD'),
    ('DH004', 'NV003', 'Lê Thị D', '0934567890', '321 Đường GHI, Hà Nội', 'Đã hoàn thành', 'Bank'),
    ('DH005', 'NV004', 'Vũ Văn E', '0945678901', '654 Đường JKL, TP.HCM', 'Đang giao', 'COD')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 14. CHI TIẾT ĐƠN HÀNG (ORDER ITEMS)
-- =====================================================

INSERT INTO chitietdonhang (madh, masp, soluong, giatrongdh) VALUES
    ('DH001', 'SP001', 1, 30000000),
    ('DH001', 'SP301', 2, 150000),
    
    ('DH002', 'SP002', 1, 22000000),
    ('DH002', 'SP101', 1, 1500000),
    
    ('DH003', 'SP201', 2, 120000),
    ('DH003', 'SP202', 1, 80000),
    ('DH003', 'SP501', 1, 320000),
    
    ('DH004', 'SP304', 1, 1200000),
    ('DH004', 'SP401', 2, 250000),
    
    ('DH005', 'SP701', 1, 450000),
    ('DH005', 'SP801', 2, 600000),
    ('DH005', 'SP902', 1, 250000)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 15. YÊU CẦU TRẢ HÀNG (RETURN REQUESTS)
-- =====================================================

INSERT INTO yeucautrahang (madh, manv, lydo, trangthai) VALUES
    ('DH001', 'NV003', 'Hàng bị lỗi', 'Đã xử lý'),
    ('DH002', 'NV004', 'Không đúng mô tả', 'Chờ xử lý')
ON CONFLICT DO NOTHING;

-- =====================================================
-- SUMMARY
-- =====================================================

-- Hiển thị số bản ghi
SELECT 'Danh Mục' as "Bảng", COUNT(*) as "Số Bản Ghi" FROM danhmuc
UNION ALL
SELECT 'Sản Phẩm', COUNT(*) FROM sanpham
UNION ALL
SELECT 'Nhân Viên', COUNT(*) FROM nhanvien
UNION ALL
SELECT 'Kho Hàng', COUNT(*) FROM kho
UNION ALL
SELECT 'Cửa Hàng', COUNT(*) FROM cuahang
UNION ALL
SELECT 'Tồn Kho', COUNT(*) FROM hangtonkho
UNION ALL
SELECT 'Đơn Hàng', COUNT(*) FROM donhang
UNION ALL
SELECT 'Chi Tiết Đơn Hàng', COUNT(*) FROM chitietdonhang
UNION ALL
SELECT 'Đánh Giá Sản Phẩm', COUNT(*) FROM danhgia
UNION ALL
SELECT 'Đánh Giá Cửa Hàng', COUNT(*) FROM danhgiacuahang
ORDER BY "Số Bản Ghi" DESC;

-- =====================================================
-- END OF SAMPLE DATA
-- =====================================================

COMMIT;
