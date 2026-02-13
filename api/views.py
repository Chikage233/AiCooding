# 必须完整导入 DRF 的 APIView 和 Response
from rest_framework.views import APIView
from rest_framework.response import Response

# 类名、方法名不能错（比如 TestView 不是 testView，get 不是 Get）
class TestView(APIView):
    # 处理 GET 请求，方法名必须是 get（小写）
    def get(self, request):
        # 返回和前端匹配的格式，无语法错误
        return Response({
            "code": 200,
            "msg": "接口调用成功！",
            "data": {"name": "AI编程辅导系统", "version": "1.0.0"}
        })