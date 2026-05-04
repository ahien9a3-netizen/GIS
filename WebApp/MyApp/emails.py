from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_refund_notification(return_request):
    """
    Gửi thông báo email khi yêu cầu hoàn tiền được chấp nhận
    """
    subject = f'Thông báo hoàn tiền đơn hàng #{return_request.DonHang.MaDH}'
    from_email = f'Smart Mart Team <no-reply@smartmart.vn>'
    to = return_request.EmailLienHe
    user_name = return_request.DonHang.TenNguoiNhan
    
    if not to and return_request.DonHang.KhachHang:
        to = return_request.DonHang.KhachHang.Email
        user_name = return_request.DonHang.KhachHang.Ten
        
    if not to and return_request.DonHang.NguoiDung:
        to = return_request.DonHang.NguoiDung.Email
        user_name = return_request.DonHang.NguoiDung.Ten
    
    if not to:
        return False

    context = {
        'user_name': user_name,
        'order_id': return_request.DonHang.MaDH,
        'request_id': return_request.MaYCTH,
        'amount': return_request.SoTienHoan,
        'note': return_request.GhiChuAdmin,
        'processed_date': return_request.NgayXuLy,
    }

    # Render HTML content
    html_content = render_to_string('MyApp/emails/refund_accepted.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
