from django.shortcuts import render

class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Nếu Django trả về mã 404 (Không tìm thấy trang)
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        
        # Nếu Django trả về mã 403 (Bị từ chối truy cập)
        if response.status_code == 403:
            return render(request, '403.html', status=403)

        return response
