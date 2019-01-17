#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from accounting import models
from django.core.validators import RegexValidator


class RegisterVerify(forms.Form):
    username = forms.CharField(min_length=4, max_length=12, error_messages={
        'required': '用户名不能为空',
        'min_length': '用户名长度不能小于4个字节',
        'max_length': '用户名长度不能大于12个字节',
    })
    password = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '密码不能为空',
        'min_length': '密码长度不能小于6位',
        'max_length': '密码长度不能大于12位'
    })
    repeat_password = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '密码不能为空',
        'min_length': '密码长度不能小于6位',
        'max_length': '密码长度不能大于12位'
    })
    email = forms.EmailField(error_messages={
        'required': '邮箱不能为空',
        'invalid': '邮箱格式错误'
    })
    telephone = forms.IntegerField(error_messages={
        'required': '手机号不能为空'
    }, validators=[RegexValidator(r'^1\d{10}$', message='手机号格式错误')])

    def clean(self):
        cleaned_data = self.cleaned_data
        pwd = self.cleaned_data.get('password', None)
        pwd2 = self.cleaned_data.get('repeat_password', None)
        user_form = self.cleaned_data.get('username', None)
        if models.UserInfo.objects.filter(username=user_form).count() > 0:
            self.add_error('username', '用户名已存在,请更换用户名注册')
        if pwd != pwd2:
            self.add_error('repeat_password', '两次输入的密码不匹配')
        return cleaned_data


class LoginVerify(forms.Form):
    username = forms.CharField(min_length=4, max_length=12, error_messages={
        'required': '用户名不能为空',
        'min_length': '用户名长度不能小于4个字节',
        'max_length': '用户名长度不能大于12个字节'
    })
    password = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '密码不能为空',
        'min_length': '密码长度不能小于6位',
        'max_length': '密码长度不能大于12位'
    })


class PassChangeVerify(forms.Form):
    old_password = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '原密码不能为空',
        'min_length': '原密码长度不能小于6位',
        'max_length': '原密码长度不能大于12位'
    })
    new_password = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '新密码不能为空',
        'min_length': '新密码长度不能小于6位',
        'max_length': '新密码长度不能大于12位'
    })
    password_repeat = forms.CharField(min_length=6, max_length=16, error_messages={
        'required': '新密码不能为空',
        'min_length': '新密码长度不能小于6位',
        'max_length': '新密码长度不能大于12位'
    })

    def clean(self):
        cleaned_data = self.cleaned_data
        old_pwd = self.cleaned_data.get('old_password', None)
        pwd = self.cleaned_data.get('new_password', None)
        pwd2 = self.cleaned_data.get('password_repeat', None)
        if old_pwd == pwd:
            self.add_error('new_password', '不能使用与先前相同的密码')
        if pwd != pwd2:
            self.add_error('password_repeat', '两次输入的密码不匹配')
        return cleaned_data
