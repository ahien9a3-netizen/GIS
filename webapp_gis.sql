-- =====================================================
-- WebApp GIS E-commerce Database Schema
-- Database: PostgreSQL + PostGIS
-- 1. EXTENSIONS

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- 2. DANH MỤC (CATEGORIES)
CREATE TABLE IF NOT EXISTS danhmuc (
    madm VARCHAR(20) PRIMARY KEY,
    tendm VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_danhmuc_tendm ON danhmuc(tendm);

-- 3. SẢN PHẨM (PRODUCTS)

CREATE TABLE IF NOT EXISTS sanpham (
    masp VARCHAR(20) PRIMARY KEY,
    ten VARCHAR(255) NOT NULL,
    image VARCHAR(255),
    danhmuc VARCHAR(20) REFERENCES danhmuc(madm) ON DELETE SET NULL,
    mieuta TEXT,
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Đang bán',
    gia DECIMAL(12, 0) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sanpham_ten ON sanpham(ten);
CREATE INDEX idx_sanpham_danhmuc ON sanpham(danhmuc);
CREATE INDEX idx_sanpham_trangthai ON sanpham(trangthai);

-- 4. ĐÁNH GIÁ SẢN PHẨM (PRODUCT RATINGS)

CREATE TABLE IF NOT EXISTS danhgia (
    id SERIAL PRIMARY KEY,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    nguoidung VARCHAR(255) NOT NULL,
    diem INTEGER NOT NULL CHECK (diem >= 1 AND diem <= 5),
    binhluan TEXT,
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_danhgia_masp ON danhgia(masp);
CREATE INDEX idx_danhgia_ngaytao ON danhgia(ngaytao);

-- 5. KHO HÀNG (WAREHOUSES)

CREATE TABLE IF NOT EXISTS kho (
    makho VARCHAR(20) PRIMARY KEY,
    ten VARCHAR(255) NOT NULL,
    loai VARCHAR(50) NOT NULL,
    diachi TEXT,
    icon VARCHAR(20),
    hinhanh VARCHAR(255)[],
    geom GEOMETRY(Point, 4326) NOT NULL,
    mota TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kho_ten ON kho(ten);
CREATE INDEX idx_kho_loai ON kho(loai);
CREATE INDEX idx_kho_geom ON kho USING GIST(geom);

-- 6. CỬA HÀNG (STORES)

CREATE TABLE IF NOT EXISTS cuahang (
    mach VARCHAR(20) PRIMARY KEY,
    ten VARCHAR(255) NOT NULL,
    loai VARCHAR(50) NOT NULL,
    icon VARCHAR(20),
    diachi TEXT,
    sdt VARCHAR(20),
    hinhanh VARCHAR(255)[],
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Hoạt động',
    geom GEOMETRY(Point, 4326) NOT NULL,
    giomocua TIME,
    giodongcua TIME,
    mota TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cuahang_ten ON cuahang(ten);
CREATE INDEX idx_cuahang_loai ON cuahang(loai);
CREATE INDEX idx_cuahang_trangthai ON cuahang(trangthai);
CREATE INDEX idx_cuahang_geom ON cuahang USING GIST(geom);

-- 7. ĐÁNH GIÁ CỬA HÀNG (STORE RATINGS)

CREATE TABLE IF NOT EXISTS danhgiacuahang (
    id SERIAL PRIMARY KEY,
    mach VARCHAR(20) NOT NULL REFERENCES cuahang(mach) ON DELETE CASCADE,
    nguoidung VARCHAR(255) NOT NULL,
    diem INTEGER NOT NULL CHECK (diem >= 1 AND diem <= 5),
    binhluan TEXT,
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_danhgiacuahang_mach ON danhgiacuahang(mach);
CREATE INDEX idx_danhgiacuahang_ngaytao ON danhgiacuahang(ngaytao);

-- 8. NHÂN VIÊN (EMPLOYEES)

CREATE TABLE IF NOT EXISTS nhanvien (
    manv VARCHAR(20) PRIMARY KEY,
    ten VARCHAR(255) NOT NULL,
    sdt VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    matkhau TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Nhân Viên',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nhanvien_ten ON nhanvien(ten);
CREATE INDEX idx_nhanvien_email ON nhanvien(email);
CREATE INDEX idx_nhanvien_role ON nhanvien(role);

-- 9. HÀNG TỒN KHO (INVENTORY)

CREATE TABLE IF NOT EXISTS hangtonkho (
    id SERIAL PRIMARY KEY,
    makho VARCHAR(20) NOT NULL REFERENCES kho(makho) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(makho, masp)
);

CREATE INDEX idx_hangtonkho_makho ON hangtonkho(makho);
CREATE INDEX idx_hangtonkho_masp ON hangtonkho(masp);

-- 10. YÊU CẦU NHẬP KHO (STOCK IN REQUESTS)

CREATE TABLE IF NOT EXISTS yeucaunhapkho (
    mayc VARCHAR(20) PRIMARY KEY,
    ngay DATE NOT NULL,
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Chờ duyệt',
    ghichu TEXT,
    manv VARCHAR(20) REFERENCES nhanvien(manv) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_yeucaunhapkho_manv ON yeucaunhapkho(manv);
CREATE INDEX idx_yeucaunhapkho_trangthai ON yeucaunhapkho(trangthai);
CREATE INDEX idx_yeucaunhapkho_ngay ON yeucaunhapkho(ngay);

-- 11. NHẬP KHO CHI TIẾT (STOCK IN DETAILS)

CREATE TABLE IF NOT EXISTS nhapkhochitiet (
    id SERIAL PRIMARY KEY,
    mayc VARCHAR(20) NOT NULL REFERENCES yeucaunhapkho(mayc) ON DELETE CASCADE,
    makho VARCHAR(20) NOT NULL REFERENCES kho(makho) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mayc, makho, masp)
);

CREATE INDEX idx_nhapkhochitiet_mayc ON nhapkhochitiet(mayc);
CREATE INDEX idx_nhapkhochitiet_makho ON nhapkhochitiet(makho);
CREATE INDEX idx_nhapkhochitiet_masp ON nhapkhochitiet(masp);

-- 12. YÊU CẦU XUẤT KHO (STOCK OUT REQUESTS)

CREATE TABLE IF NOT EXISTS yeucauxuatkho (
    mapx VARCHAR(20) PRIMARY KEY,
    ngay DATE NOT NULL DEFAULT CURRENT_DATE,
    lydo VARCHAR(50) NOT NULL DEFAULT 'Bán hàng',
    madh VARCHAR(20),
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Mới',
    ghichu TEXT,
    manv VARCHAR(20) NOT NULL REFERENCES nhanvien(manv) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_yeucauxuatkho_manv ON yeucauxuatkho(manv);
CREATE INDEX idx_yeucauxuatkho_trangthai ON yeucauxuatkho(trangthai);
CREATE INDEX idx_yeucauxuatkho_ngay ON yeucauxuatkho(ngay);

-- 13. XUẤT KHO CHI TIẾT (STOCK OUT DETAILS)

CREATE TABLE IF NOT EXISTS xuatkhochitiet (
    id SERIAL PRIMARY KEY,
    mapx VARCHAR(20) NOT NULL REFERENCES yeucauxuatkho(mapx) ON DELETE CASCADE,
    makho VARCHAR(20) NOT NULL REFERENCES kho(makho) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mapx, makho, masp)
);

CREATE INDEX idx_xuatkhochitiet_mapx ON xuatkhochitiet(mapx);
CREATE INDEX idx_xuatkhochitiet_makho ON xuatkhochitiet(makho);
CREATE INDEX idx_xuatkhochitiet_masp ON xuatkhochitiet(masp);

-- 14. GIỎ HÀNG (SHOPPING CART)

CREATE TABLE IF NOT EXISTS giohang (
    id SERIAL PRIMARY KEY,
    manv VARCHAR(20) REFERENCES nhanvien(manv) ON DELETE CASCADE,
    session_id VARCHAR(255),
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ngaycapnhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_giohang_manv ON giohang(manv);
CREATE INDEX idx_giohang_session_id ON giohang(session_id);

-- 15. CHI TIẾT GIỎ HÀNG (CART ITEMS)

CREATE TABLE IF NOT EXISTS chitietgiohang (
    id SERIAL PRIMARY KEY,
    magh INTEGER NOT NULL REFERENCES giohang(id) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(magh, masp)
);

CREATE INDEX idx_chitietgiohang_magh ON chitietgiohang(magh);
CREATE INDEX idx_chitietgiohang_masp ON chitietgiohang(masp);

-- 16. ĐƠN HÀNG (ORDERS)

CREATE TABLE IF NOT EXISTS donhang (
    madh VARCHAR(20) PRIMARY KEY,
    manv VARCHAR(20) REFERENCES nhanvien(manv) ON DELETE SET NULL,
    tennguoinhan VARCHAR(255) NOT NULL,
    sdt_nhan VARCHAR(20) NOT NULL,
    diachi_nhan TEXT NOT NULL,
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Đang xử lý',
    phuongthuctt VARCHAR(50) NOT NULL DEFAULT 'COD',
    ghichu TEXT,
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE donhang ADD COLUMN IF NOT EXISTS tongtien DECIMAL(12, 0) DEFAULT 0;
ALTER TABLE donhang RENAME COLUMN phuongthuctt TO pt_thanhtoan;
CREATE INDEX idx_donhang_manv ON donhang(manv);
CREATE INDEX idx_donhang_trangthai ON donhang(trangthai);
CREATE INDEX idx_donhang_ngaytao ON donhang(ngaytao);

-- 17. CHI TIẾT ĐƠN HÀNG (ORDER ITEMS)

CREATE TABLE IF NOT EXISTS chitietdonhang (
    id SERIAL PRIMARY KEY,
    madh VARCHAR(20) NOT NULL REFERENCES donhang(madh) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL,
    giatrongdh DECIMAL(12, 0) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(madh, masp)
);

ALTER TABLE chitietdonhang RENAME COLUMN giatrongdh TO giaban;
CREATE INDEX idx_chitietdonhang_madh ON chitietdonhang(madh);
CREATE INDEX idx_chitietdonhang_masp ON chitietdonhang(masp);

-- 18. YÊU CẦU TRẢ HÀNG (RETURN REQUESTS)

CREATE TABLE IF NOT EXISTS yeucautrahang (
    id SERIAL PRIMARY KEY,
    madh VARCHAR(20) NOT NULL REFERENCES donhang(madh) ON DELETE CASCADE,
    manv VARCHAR(20) REFERENCES nhanvien(manv) ON DELETE SET NULL,
    lydo TEXT NOT NULL,
    trangthai VARCHAR(50) NOT NULL DEFAULT 'Chờ xử lý',
    ghichu TEXT,
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_yeucautrahang_madh ON yeucautrahang(madh);
CREATE INDEX idx_yeucautrahang_trangthai ON yeucautrahang(trangthai);
CREATE INDEX idx_yeucautrahang_ngaytao ON yeucautrahang(ngaytao);

-- 19. PHÂN BỔ CUNG CẤP (SUPPLY DISTRIBUTION)

CREATE TABLE IF NOT EXISTS phanbocungcap (
    id SERIAL PRIMARY KEY,
    mach VARCHAR(20) NOT NULL REFERENCES cuahang(mach) ON DELETE CASCADE,
    makho VARCHAR(20) NOT NULL REFERENCES kho(makho) ON DELETE CASCADE,
    khoang_cach DECIMAL(5, 1),
    thoi_gian INTEGER,
    uu_tien INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mach, makho)
);

CREATE INDEX idx_phanbocungcap_mach ON phanbocungcap(mach);
CREATE INDEX idx_phanbocungcap_makho ON phanbocungcap(makho);
CREATE INDEX idx_phanbocungcap_uu_tien ON phanbocungcap(uu_tien);

-- 20. LEGACY STORES TABLE

CREATE TABLE IF NOT EXISTS stores_legacy (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    lat FLOAT DEFAULT 10.7769,
    lon FLOAT DEFAULT 106.7009,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- VIEWS
-- =====================================================

-- View: Tồn kho chi tiết
DROP VIEW IF EXISTS v_hangtonkho_detail CASCADE;
CREATE VIEW v_hangtonkho_detail AS
SELECT 
    htk.id,
    k.makho,
    k.ten as ten_kho,
    sp.masp,
    sp.ten as ten_sanpham,
    dm.tendm as danh_muc,
    htk.soluong,
    sp.gia,
    (htk.soluong * sp.gia) as tong_gia_tri,
    htk.created_at,
    htk.updated_at
FROM hangtonkho htk
JOIN kho k ON htk.makho = k.makho
JOIN sanpham sp ON htk.masp = sp.masp
JOIN danhmuc dm ON sp.danhmuc = dm.madm;

-- View: Đơn hàng chi tiết
DROP VIEW IF EXISTS v_donhang_detail CASCADE;
CREATE VIEW v_donhang_detail AS
SELECT 
    dh.madh,
    dh.manv,
    nv.ten as ten_nhanvien,
    dh.tennguoinhan,
    dh.sdt_nhan,
    dh.diachi_nhan,
    dh.trangthai,
    dh.phuongthuctt,
    dh.ngaytao,
    COUNT(DISTINCT ctdh.id) as so_san_pham,
    SUM(ctdh.soluong) as tong_so_luong,
    SUM(ctdh.soluong * ctdh.giatrongdh) as tong_tien
FROM donhang dh
LEFT JOIN nhanvien nv ON dh.manv = nv.manv
LEFT JOIN chitietdonhang ctdh ON dh.madh = ctdh.madh
GROUP BY dh.madh, dh.manv, nv.ten, dh.tennguoinhan, dh.sdt_nhan, dh.diachi_nhan, 
         dh.trangthai, dh.phuongthuctt, dh.ngaytao;

-- View: Đánh giá sản phẩm
DROP VIEW IF EXISTS v_danhgia_sanpham CASCADE;
CREATE VIEW v_danhgia_sanpham AS
SELECT 
    sp.masp,
    sp.ten,
    COUNT(dg.id) as so_danh_gia,
    ROUND(AVG(dg.diem), 2) as diem_trung_binh,
    MAX(dg.diem) as diem_cao_nhat,
    MIN(dg.diem) as diem_thap_nhat
FROM sanpham sp
LEFT JOIN danhgia dg ON sp.masp = dg.masp
GROUP BY sp.masp, sp.ten;

-- FUNCTIONS / PROCEDURES

-- Function: Cập nhật tồn kho sau khi nhập
CREATE OR REPLACE FUNCTION update_inventory_after_import()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO hangtonkho (makho, masp, soluong)
    VALUES (NEW.makho, NEW.masp, NEW.soluong)
    ON CONFLICT (makho, masp) 
    DO UPDATE SET soluong = hangtonkho.soluong + NEW.soluong,
                  updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_inventory_after_import ON nhapkhochitiet;

CREATE TRIGGER trg_update_inventory_after_import
AFTER INSERT ON nhapkhochitiet
FOR EACH ROW
EXECUTE FUNCTION update_inventory_after_import();

-- Function: Giảm tồn kho sau khi xuất
CREATE OR REPLACE FUNCTION update_inventory_after_export()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE hangtonkho
    SET soluong = soluong - NEW.soluong,
        updated_at = CURRENT_TIMESTAMP
    WHERE makho = NEW.makho AND masp = NEW.masp;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_inventory_after_export ON xuatkhochitiet;

CREATE TRIGGER trg_update_inventory_after_export
AFTER INSERT ON xuatkhochitiet
FOR EACH ROW
EXECUTE FUNCTION update_inventory_after_export();

-- =====================================================
-- END OF SCHEMA
-- =====================================================


-- =====================================================
-- Sample Data for WebApp E-commerce Database
-- Dữ liệu mẫu cho hệ thống bán hàng
-- =====================================================

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
;

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
;

-- =====================================================
-- 3. NHÂN VIÊN (EMPLOYEES)
-- =====================================================

INSERT INTO nhanvien (manv, ten, email, sdt, matkhau, role) VALUES
    ('NV001', 'Nguyễn Văn Admin', 'admin@webapp.com', '0901234567', 'hashed_admin_pwd', 'Admin'),
    ('NV002', 'Lê Thị Kế Toán', 'ketoan@webapp.com', '0902345678', 'hashed_kt_pwd', 'Kế Toán'),
    ('NV003', 'Trần Văn Hùng', 'hung@webapp.com', '0903456789', 'hashed_nv_pwd', 'Nhân Viên'),
    ('NV004', 'Phạm Thị Hoa', 'hoa@webapp.com', '0904567890', 'hashed_nv_pwd', 'Nhân Viên'),
    ('NV005', 'Vũ Đình Minh', 'minh@webapp.com', '0905678901', 'hashed_user_pwd', 'User')
;

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
;

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
;

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
;

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
;

-- =====================================================
-- 8. YÊU CẦU NHẬP KHO (STOCK IN)
-- =====================================================

INSERT INTO yeucaunhapkho (mayc, ngay, trangthai, manv) VALUES
    ('YC001', '2024-04-01', 'Đã duyệt', 'NV001'),
    ('YC002', '2024-04-05', 'Đã duyệt', 'NV002'),
    ('YC003', '2024-04-10', 'Chờ duyệt', 'NV003'),
    ('YC004', '2024-04-15', 'Đã duyệt', 'NV001'),
    ('YC005', '2024-04-20', 'Đã duyệt', 'NV004')
;

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
;

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
;

-- =====================================================
-- 11. ĐÁNH GIÁ CỬA HÀNG (STORE RATINGS)
-- =====================================================

INSERT INTO danhgiacuahang (mach, nguoidung, diem, binhluan) VALUES
    ('CH001', 'Khách hàng 1', 5, 'Cửa hàng sạch sẽ, nhân viên thân thiện'),
    ('CH001', 'Khách hàng 2', 4, 'Hàng hóa đa dạng'),
    ('CH002', 'Khách hàng 3', 5, 'Sản phẩm điện tử chính hãng'),
    ('CH003', 'Khách hàng 4', 4, 'Giá cạnh tranh'),
    ('CH005', 'Khách hàng 5', 5, 'Quần áo đẹp, giá tốt')
;

-- =====================================================
-- 12. GIỎ HÀNG VÀ CHI TIẾT (SHOPPING CART)
-- =====================================================

INSERT INTO giohang (manv, session_id) VALUES
    ('NV005', 'session_001'),
    (NULL, 'session_guest_001'),
    (NULL, 'session_guest_002')
;

-- =====================================================
-- 13. ĐƠN HÀNG (ORDERS)
-- =====================================================

INSERT INTO donhang (madh, manv, tennguoinhan, sdt_nhan, diachi_nhan, trangthai, phuongthuctt) VALUES
    ('DH001', 'NV003', 'Trần Văn A', '0912345678', '123 Đường ABC, Hà Nội', 'Đã hoàn thành', 'COD'),
    ('DH002', 'NV003', 'Nguyễn Thị B', '0987654321', '456 Đường XYZ, TP.HCM', 'Đang giao', 'MoMo'),
    ('DH003', 'NV004', 'Phạm Văn C', '0923456789', '789 Đường DEF, Đà Nẵng', 'Đang xử lý', 'COD'),
    ('DH004', 'NV003', 'Lê Thị D', '0934567890', '321 Đường GHI, Hà Nội', 'Đã hoàn thành', 'Bank'),
    ('DH005', 'NV004', 'Vũ Văn E', '0945678901', '654 Đường JKL, TP.HCM', 'Đang giao', 'COD')
;

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
;

-- =====================================================
-- 15. YÊU CẦU TRẢ HÀNG (RETURN REQUESTS)
-- =====================================================

INSERT INTO yeucautrahang (madh, manv, lydo, trangthai) VALUES
    ('DH001', 'NV003', 'Hàng bị lỗi', 'Đã xử lý'),
    ('DH002', 'NV004', 'Không đúng mô tả', 'Chờ xử lý')
;

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



