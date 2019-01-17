#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import HttpResponse
from django.utils.decorators import method_decorator
from accounting.base_handler import BaseHandler
from django.db.models import Sum
from accounting import models
from accounting import form_verify
import json


def login_required(func):
    """
    登录认证装饰器
    :param func:
    :return:
    """

    def wrapper(request, *args, **kwargs):
        if request.session.get('username', None):
            return func(request, *args, **kwargs)
        else:
            return_data = {'status': 'False', 'message': '请登陆后再进行操作', 'data': ''}
            return HttpResponse(json.dumps(return_data, ensure_ascii=False, indent=4), content_type='application/json',
                                charset='utf-8')

    return wrapper


class Login(BaseHandler):
    """
    实现登录类
    """

    def get(self, request):
        """
        get请求暂时未做处理
        :param request:
        :return:
        """
        if request.session.get('username', None):
            return self.http_response(status='False', message='您已经登录，请勿重复登录，如需切换账号，请退出后重新登录。', data='')
        else:
            return self.http_response(status='True', message='', data='')

    def post(self, request):
        """
        对于使用POST数据传递来的用户名和密码，在数据库中查询是否存在，若存在，写入session，设置session超时时间
        :param request:
        :return:
        """
        # 获取POST传递过来的 username 及 password
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        # 获取是否传递 session_expiry 值
        session_expiry = request.POST.get('session_expiry', None)
        # 到数据库中针对传递过来的账户密码进行查询，获取第一个
        obj = models.UserInfo.objects.filter(username=username, password=password).first()
        if obj:
            # 如果查得到，设置 session 及 超时时间
            request.session['username'] = username
            request.session['is_login'] = True
            if session_expiry == '1':
                request.session.set_expiry(604800)
            # 返回提示信息
            return self.http_response(status='True', message='登录成功', data='')
        else:
            return self.http_response(status='False', message='用户名或密码错误', data='')


@method_decorator(login_required, name='dispatch')
class Logout(BaseHandler):
    """
    实现注销/退出类
    """

    def get(self, request):
        """
        使用get方法时，清除session
        :param request:
        :return:
        """
        # 判断当前用户session中是否含有username
        if request.session.get('username', None):
            request.session.clear()
            return self.http_response(status='True', message='注销成功', data='')
        else:
            return self.http_response(status='False', message='你没登录你注销个屁啊', data='')


class Register(BaseHandler):
    """
    用户注册实现类
    """

    def get(self):
        """
        get请求暂未处理
        :param :
        :return:
        """
        return self.http_response(status='True', message='', data='')

    def post(self, request):
        """
        接收POST得到的请求，进行格式校验，若校验失败返回错误信息，若校验成功，将注册信息写入数据库中
        :param request:
        :return:
        """
        # 对接收到的POST数据进行表单验证
        obj = form_verify.RegisterVerify(request.POST)
        if obj.is_valid():
            # 处理用户信息字段
            register_ip = self.get_client_ip(request)
            register_time = self.get_now_time()
            register_user_info = obj.cleaned_data
            register_user_info['register_time'] = register_time
            register_user_info['register_ip'] = register_ip
            register_user_info.pop('repeat_password')
            # 将用户信息字典写入数据库中
            models.UserInfo.objects.create(**register_user_info)
            return self.http_response(status='True', message='注册成功', data='')
        else:
            # 如果Form校验失败，返回报错信息及空数据
            return self.http_response(status='False', message=obj.errors, data='')


@method_decorator(login_required, name='dispatch')
class RecordOperate(BaseHandler):

    def get(self, request):
        """
        接受get请求，返回当前用户操作记录，按照操作顺序排序
        :param request:
        :return:
        """
        # 获取当前用户ID
        user_id = self.get_user_id(request)
        # 按照id逆向排序查询到的参数，并返回数据
        record_data = models.Record.objects.filter(user_id_id=user_id).order_by('-id').values()
        return self.http_response(status='True', message='查询成功', data=list(record_data))

    def post(self, request):
        """
        post请求允许用户新增或修改数据
        operate_status = 0 时为添加数据
                       = 1 时为修改数据
        operate_type = 0 时为收入
                     = 1 时为支出
        :param request:
        :return:
        """
        # 获取当前用户ID
        user_id = self.get_user_id(request)
        # json解析收到的POST包
        received_data = json.loads(request.body)
        # 获取当前时间，用于数据库记录
        operate_time = self.get_now_time()
        received_data['operate_time'] = operate_time
        received_data['user_id_id'] = user_id
        # 查询数据库中该钱包所余额
        money = models.Money.objects.filter(wallet_type=received_data['operate_account']).values()
        # 添加新数据
        if received_data['operate_status'] == 0:
            received_data.pop('operate_status')
            models.Record.objects.create(**received_data)

            # 如果为支出，将数值变为负数
            if received_data['operate_type'] == 1:
                received_data['operate_amount'] = 0 - received_data['operate_amount']
            new_money = money[0]['wallet_money'] + received_data['operate_amount']
            models.Money.objects.filter(wallet_type=received_data['operate_account']).update(
                    wallet_money=new_money)
            times_value = models.UserInfo.objects.filter(user_id=user_id).values()[0]['times'] + 1
            models.UserInfo.objects.filter(user_id=user_id).update(times=times_value)
            # 重新查询数据并返回
            record_data = models.Record.objects.filter(user_id_id=user_id).order_by('-id').values()
            return self.http_response(status='True', message='添加成功', data=list(record_data))
        # 修改旧数据
        elif received_data['operate_status'] == 1:
            received_data.pop('operate_status')
            # 先根据id查询旧数据
            old_record = models.Record.objects.filter(id=received_data['id']).values()[0]
            old_record_account = old_record['operate_account']
            old_record_amount = old_record['operate_amount']
            old_record_type = old_record['operate_type']
            now_money = models.Money.objects.filter(wallet_type=old_record_account).values()[0]
            if old_record_type == 1:
                old_record_amount = 0 - old_record_amount
            back_money = now_money['wallet_money'] - old_record_amount
            # 回滚钱包数据
            models.Money.objects.filter(wallet_type=old_record_account).update(wallet_money=back_money)
            # 按照新数据更新数据库字段
            models.Record.objects.filter(id=received_data['id']).update(**received_data)
            # 根据新数据更改钱包
            if received_data['operate_type'] == 1:
                received_data['operate_amount'] = 0 - received_data['operate_amount']
            new_money = money[0]['wallet_money'] + received_data['operate_amount']
            models.Money.objects.filter(wallet_type=received_data['operate_account']).update(
                    wallet_money=new_money)
            # 重新查询数据并返回
            record_data = models.Record.objects.filter(user_id_id=user_id).order_by('-id').values()
            return self.http_response(status='True', message='修改成功', data=list(record_data))
        # 删除数据
        elif received_data['operate_status'] == 2:
            received_data.pop('operate_status')
            # 先根据id查询旧数据
            old_record = models.Record.objects.filter(id=received_data['id']).values()[0]
            old_record_account = old_record['operate_account']
            old_record_amount = old_record['operate_amount']
            old_record_type = old_record['operate_type']
            now_money = models.Money.objects.filter(wallet_type=old_record_account).values()[0]
            if old_record_type == 1:
                old_record_amount = 0 - old_record_amount
            back_money = now_money['wallet_money'] - old_record_amount
            # 回滚钱包数据
            models.Money.objects.filter(wallet_type=old_record_account).update(wallet_money=back_money)
            # 按照新数据更新数据库字段
            models.Record.objects.filter(id=received_data['id']).delete()
            # 重新查询数据并返回
            record_data = models.Record.objects.filter(user_id_id=user_id).order_by('-id').values()
            return self.http_response(status='True', message='修改成功', data=list(record_data))
        # 其他非常规字符返回错误信息
        else:
            record_data = models.Record.objects.filter(user_id_id=user_id).order_by('-id').values()
            return self.http_response(status='False', message='请输入正确的操作状态', data=list(record_data))


@method_decorator(login_required, name='dispatch')
class MoneyOperate(BaseHandler):

    def get(self, request):
        """
        使用get方法获取
        :param request:
        :return:
        """
        user_id = self.get_user_id(request)
        wallet_data = models.Money.objects.filter(user_id_id=user_id).values()
        return self.http_response(status='True', message='查询成功', data=list(wallet_data))

    def post(self, request):
        """
        使用post方法直接创建钱包，或更改账户余额
        operate_status = 0 时创建新钱包及金额
                       = 1 时更改账户余额
        :param request:
        :return:
        """
        user_id = self.get_user_id(request)
        received_data = json.loads(request.body)
        received_data['user_id_id'] = user_id
        # 如果创建新钱包
        if received_data['operate_status'] == 0:
            # 删除掉 operate_status 字段
            received_data.pop('operate_status')
            # 先在数据库中查询是否有同名钱包
            obj = models.UserInfo.objects.filter(wallet_type=received_data['wallet_type']).first()
            # 如果没有
            if not obj:
                # 在Money数据库中创建数据
                models.Money.objects.create(**received_data)
                # 重新查询数据并返回
                wallet_data = models.Money.objects.filter(user_id_id=user_id).values('wallet_type', 'wallet_money')
                return self.http_response(status='True', message='创建钱包成功', data=list(wallet_data))
            # 如果有同名钱包
            else:
                return self.http_response(status='True', message='已经有同名账户，请更换其他名称', data='')
        # 如果直接更改账户余额
        elif received_data['operate_status'] == 1:
            # 删除掉 operate_status 字段
            received_data.pop('operate_status')
            # 获取响应钱包所在字段，更新钱包内容
            models.Money.objects.filter(wallet_type=received_data['wallet_type']).update(**received_data)
            # 重新查询数据并返回
            wallet_data = models.Money.objects.filter(user_id_id=user_id).values('wallet_type', 'wallet_money')
            return self.http_response(status='True', message='更改成功', data=list(wallet_data))
        # 如果删除钱包
        elif received_data['operate_status'] == 2:
            # 删除掉 operate_status 字段
            received_data.pop('operate_status')
            # 删除钱包内容
            models.Money.objects.filter(user_id_id=user_id, wallet_type=received_data['wallet_type']).delete()
            # 重新查询数据并返回
            wallet_data = models.Money.objects.filter(user_id_id=user_id).values('wallet_type', 'wallet_money')
            return self.http_response(status='True', message='删除成功', data=list(wallet_data))
        # 其他非常规字符返回错误信息
        else:
            return self.http_response(status='False', message='请输入正确的操作状态', data='')


@method_decorator(login_required, name='dispatch')
class PasswordChange(BaseHandler):
    """
    用户密码修改实现类
    """
    def get(self):
        return self.http_response(status='True', message='', data='')

    def post(self, request):
        username = request.session.get('username')
        obj = form_verify.PassChangeVerify(request.POST)
        # 对表单进行校验
        if obj.is_valid():
            pass_change_info = obj.cleaned_data
            old_password = pass_change_info.get('old_password')
            # 到数据库中查询账户密码是否存在
            result = models.UserInfo.objects.filter(username=username, password=old_password).first()
            if result:
                pass_change_info.pop('password_repeat')
                # 更新数据库，更改新密码
                models.UserInfo.objects.filter(username=username).update(password=pass_change_info.get('new_password'))
                # 清除 session
                request.session.clear()
                return self.http_response(status='True', message='修改成功，请重新登录', data='')
            else:
                return self.http_response(status='False', message={"old_password": ["旧密码填写错误"]}, data='')
        else:
            return self.http_response(status='False', message=obj.errors, data='')


@method_decorator(login_required, name='dispatch')
class GetReport(BaseHandler):
    """
    生成报表实现类
    """

    def get(self, request):
        user_id = self.get_user_id(request)
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')

        # 定义聚合函数，查询收入/支出不同分类金额总和
        def calculate(operate_type, stime, etime):
            sum_amount = models.Record.objects.values('remarks').filter(
                user_id=user_id,
                operate_type=operate_type,
                operate_time__range=[stime, etime]
                ).annotate(all=Sum('operate_amount'))
            return sum_amount

        # 时间内总支出
        expenditure = list(calculate(1, start_time, end_time))
        print(expenditure)
        # 时间内总收入
        gaining = list(calculate(0, start_time, end_time))
        report = {
            "收入明细": gaining,
            "支出明细": expenditure
        }
        return self.http_response(status='True', message='报表生成成功', data=report)
