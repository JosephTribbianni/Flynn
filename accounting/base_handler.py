#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

from django.shortcuts import HttpResponse
from django import views
from accounting import models
import time
import datetime
import json


class BaseHandler(views.View):
    """
    封装BaseHandler类，继承views.View，再由视图下实现方法继承
    """

    @staticmethod
    def get_now_time():
        """
        获取当前时间
        :return:
        """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    @staticmethod
    def get_client_ip(this_request):
        """
        获取用户当前IP地址
        :param this_request:
        :return:
        """
        x_forwarded_for = this_request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = this_request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def http_response(status, message, data):
        """
        使用HttpResponse返回JSON格式数据
        :param status:
        :param message:
        :param data:
        :return:
        """
        return_data = {'status': status, 'message': message, 'data': data}
        return HttpResponse(json.dumps(return_data, ensure_ascii=False, indent=4, cls=CJsonEncoder),
                            content_type='application/json',
                            charset='utf-8')

    @staticmethod
    def get_user_id(request):
        """
        根据session中的用户名返回用户ID
        :param request:
        :return:
        """
        return models.UserInfo.objects.get(username=request.session.get('username')).user_id


class CJsonEncoder(json.JSONEncoder):
    """
    自定义JSON序列化datatime类
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)
