-- =====================================================
-- WebApp GIS E-commerce Database Schema
-- Database: PostgreSQL + PostGIS
-- Created: 2024
-- =====================================================

-- =====================================================
-- 1. EXTENSIONS
-- =====================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- =====================================================
-- 2. DANH MỤC (CATEGORIES)
-- =====================================================

CREATE TABLE IF NOT EXISTS danhmuc (
    madm VARCHAR(20) PRIMARY KEY,
    tendm VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_danhmuc_tendm ON danhmuc(tendm);

-- =====================================================
-- 3. SẢN PHẨM (PRODUCTS)
-- =====================================================

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

-- =====================================================
-- 4. ĐÁNH GIÁ SẢN PHẨM (PRODUCT RATINGS)
-- =====================================================

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

-- =====================================================
-- 5. KHO HÀNG (WAREHOUSES)
-- =====================================================

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

-- =====================================================
-- 6. CỬA HÀNG (STORES)
-- =====================================================

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

-- =====================================================
-- 7. ĐÁNH GIÁ CỬA HÀNG (STORE RATINGS)
-- =====================================================

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

-- =====================================================
-- 8. NHÂN VIÊN (EMPLOYEES)
-- =====================================================

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

-- =====================================================
-- 9. HÀNG TỒN KHO (INVENTORY)
-- =====================================================

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

-- =====================================================
-- 10. YÊU CẦU NHẬP KHO (STOCK IN REQUESTS)
-- =====================================================

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

-- =====================================================
-- 11. NHẬP KHO CHI TIẾT (STOCK IN DETAILS)
-- =====================================================

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

-- =====================================================
-- 12. YÊU CẦU XUẤT KHO (STOCK OUT REQUESTS)
-- =====================================================

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

-- =====================================================
-- 13. XUẤT KHO CHI TIẾT (STOCK OUT DETAILS)
-- =====================================================

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

-- =====================================================
-- 14. GIỎ HÀNG (SHOPPING CART)
-- =====================================================

CREATE TABLE IF NOT EXISTS giohang (
    id SERIAL PRIMARY KEY,
    manv VARCHAR(20) REFERENCES nhanvien(manv) ON DELETE CASCADE,
    session_id VARCHAR(255),
    ngaytao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ngaycapnhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_giohang_manv ON giohang(manv);
CREATE INDEX idx_giohang_session_id ON giohang(session_id);

-- =====================================================
-- 15. CHI TIẾT GIỎ HÀNG (CART ITEMS)
-- =====================================================

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

-- =====================================================
-- 16. ĐƠN HÀNG (ORDERS)
-- =====================================================

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

CREATE INDEX idx_donhang_manv ON donhang(manv);
CREATE INDEX idx_donhang_trangthai ON donhang(trangthai);
CREATE INDEX idx_donhang_ngaytao ON donhang(ngaytao);

-- =====================================================
-- 17. CHI TIẾT ĐƠN HÀNG (ORDER ITEMS)
-- =====================================================

CREATE TABLE IF NOT EXISTS chitietdonhang (
    id SERIAL PRIMARY KEY,
    madh VARCHAR(20) NOT NULL REFERENCES donhang(madh) ON DELETE CASCADE,
    masp VARCHAR(20) NOT NULL REFERENCES sanpham(masp) ON DELETE CASCADE,
    soluong INTEGER NOT NULL,
    giatrongdh DECIMAL(12, 0) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(madh, masp)
);

CREATE INDEX idx_chitietdonhang_madh ON chitietdonhang(madh);
CREATE INDEX idx_chitietdonhang_masp ON chitietdonhang(masp);

-- =====================================================
-- 18. YÊU CẦU TRẢ HÀNG (RETURN REQUESTS)
-- =====================================================

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

-- =====================================================
-- 19. PHÂN BỔ CUNG CẤP (SUPPLY DISTRIBUTION)
-- =====================================================

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

-- =====================================================
-- 20. LEGACY STORES TABLE
-- =====================================================

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
-- SAMPLE DATA / DỮ LIỆU MẪU
-- =====================================================

-- Insert sample categories
INSERT INTO danhmuc (madm, tendm) VALUES
    ('DM001', 'Điện Tử'),
    ('DM002', 'Gia Dụng'),
    ('DM003', 'Thực Phẩm'),
    ('DM004', 'Quần Áo')
ON CONFLICT DO NOTHING;

-- Insert sample products
INSERT INTO sanpham (masp, ten, danhmuc, gia, trangthai) VALUES
    ('SP001', 'iPhone 15 Pro', 'DM001', 25000000, 'Đang bán'),
    ('SP002', 'Samsung TV 55', 'DM001', 15000000, 'Đang bán'),
    ('SP003', 'Nồi cơm điện', 'DM002', 500000, 'Đang bán'),
    ('SP004', 'Gạo Việt Nam', 'DM003', 50000, 'Đang bán'),
    ('SP005', 'Áo thun nam', 'DM004', 100000, 'Đang bán')
ON CONFLICT DO NOTHING;

-- Insert sample employees
INSERT INTO nhanvien (manv, ten, email, matkhau, role) VALUES
    ('NV001', 'Nguyễn Admin', 'admin@webapp.com', 'hashed_password_1', 'Admin'),
    ('NV002', 'Lê Kế Toán', 'ketoan@webapp.com', 'hashed_password_2', 'Kế Toán'),
    ('NV003', 'Trần Nhân Viên', 'staff@webapp.com', 'hashed_password_3', 'Nhân Viên')
ON CONFLICT DO NOTHING;

-- Insert sample warehouses
INSERT INTO kho (makho, ten, loai, diachi, geom) VALUES
    ('KHO001', 'Kho Tổng Hà Nội', 'Kho Tổng', '123 Đường Tây Sơn, Đống Đa, Hà Nội', ST_GeomFromText('POINT(106.7009 10.7769)', 4326)),
    ('KHO002', 'Kho Chi Nhánh Hồ Chí Minh', 'Kho Chi Nhánh', '456 Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM', ST_GeomFromText('POINT(106.7223 10.8020)', 4326))
ON CONFLICT DO NOTHING;

-- Insert sample stores
INSERT INTO cuahang (mach, ten, loai, diachi, sdt, trangthai, geom) VALUES
    ('CH001', 'Cửa Hàng Tiện Lợi Hà Nội', 'Tiện Lợi', '789 Đường Ngô Thì Nhậm, Hai Bà Trưng, Hà Nội', '0243123456', 'Hoạt động', ST_GeomFromText('POINT(106.7040 10.7850)', 4326)),
    ('CH002', 'Cửa Hàng Điện Tử TP.HCM', 'Điện Tử', '101 Pasteur, Quận 1, TP.HCM', '0283456789', 'Hoạt động', ST_GeomFromText('POINT(106.6955 10.7813)', 4326))
ON CONFLICT DO NOTHING;

-- Insert sample inventory
INSERT INTO hangtonkho (makho, masp, soluong) VALUES
    ('KHO001', 'SP001', 50),
    ('KHO001', 'SP002', 30),
    ('KHO001', 'SP003', 100),
    ('KHO002', 'SP001', 40),
    ('KHO002', 'SP004', 200)
ON CONFLICT DO NOTHING;

-- Insert sample supply distribution
INSERT INTO phanbocungcap (mach, makho, uu_tien) VALUES
    ('CH001', 'KHO001', 1),
    ('CH002', 'KHO001', 1),
    ('CH002', 'KHO002', 2)
ON CONFLICT DO NOTHING;

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

-- =====================================================
-- FUNCTIONS / PROCEDURES
-- =====================================================

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
-- PERMISSIONS (Optional - adjust based on your needs)
-- =====================================================

-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO webapp_user;
-- GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO webapp_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO webapp_user;

-- =====================================================
-- END OF SCHEMA
-- =====================================================

COMMIT;
