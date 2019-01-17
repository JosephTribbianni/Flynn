#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models


class UserInfo(models.Model):
    """
    创建用户信息数据库
    """
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    register_time = models.DateTimeField()
    register_ip = models.GenericIPAddressField(protocol='IPv4')
    email = models.CharField(max_length=32)
    telephone = models.CharField(max_length=32)
    times = models.IntegerField(default=0)

    def __str__(self):
        return '{0},{1},{2},{3},{4},{5},{6},{7}'.format(self.user_id, self.username, self.password, self.register_time,
                                                        self.register_ip, self.email, self.telephone, self.times)


class Record(models.Model):
    """
    创建收支记录数据库
    """
    user_id = models.ForeignKey(to=UserInfo, to_field='user_id', on_delete=models.CASCADE)
    operate_type = models.CharField(max_length=32)
    operate_account = models.CharField(max_length=32)
    operate_amount = models.FloatField(default=0)
    operate_time = models.DateTimeField()
    remarks = models.CharField(max_length=32)


class Money(models.Model):
    """
    创建钱包及余额数据库
    """
    user_id = models.ForeignKey(to=UserInfo, to_field='user_id', on_delete=models.CASCADE)
    wallet_type = models.CharField(max_length=32)
    wallet_money = models.DecimalField(default=0, max_digits=7, decimal_places=2)
