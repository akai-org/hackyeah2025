from django.urls import re_path
from trends.views import TrendView

urlpatterns = [
    re_path(r"trend(?P<route_name>)", TrendView.as_view(), name="trend_view")
]
