# -*- coding: utf-8 -*-
"""model_bulding.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DYSO1_vINIrVLzff7866BDWDpaGH36_c
"""

import torch
import torch.nn as nn
import math

torch.__version__

"""##CNN model (Combination of DeepLabv3+ and SqueezeNet)"""


class firem(nn.Module):
  def __init__(self, in_channel, sq_f, ex_f):
    super(firem, self).__init__()
    self.conv1 = nn.Conv2d(in_channel, sq_f, kernel_size=1, stride=1, bias=False)
    self.bn1 = nn.BatchNorm2d(sq_f)
    self.relu1 = nn.ReLU(inplace=True)
    self.conv2 = nn.Conv2d(sq_f, ex_f, kernel_size=1, stride=1, bias=False)
    self.bn2 = nn.BatchNorm2d(ex_f)
    self.conv3 = nn.Conv2d(sq_f, ex_f, kernel_size=3, stride=1, padding=1, bias=False)
    self.bn3 = nn.BatchNorm2d(ex_f)
    self.relu2 = nn.ReLU(inplace = True)


    ## MSR initialization
    for m in self.modules():
      if isinstance(m, nn.Conv2d):
        n = m.kernel_size[0]*m.kernel_size[1]*m.in_channels
        m.weight.data.normal_(0, math.sqrt(2./n))

  def forward(self,x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu1(x)

    y_1 = self.conv2(x)
    y_1 = self.bn2(y_1)
    y_1 = self.relu1(y_1)

    y_2 = self.conv3(x)
    y_2 = self.bn3(y_2)
    y_2 = self.relu1(y_2)

    out = torch.cat([y_1, y_2],1)
    out = self.relu2(out)

    return out



class snet(nn.Module):
  def __init__ (self, in_channel):
    super(snet,self).__init__()
    self.sconv1 = nn.Conv2d(in_channel, 12, kernel_size=3, stride=1, padding=1, bias=False)
    self.sbn1 = nn.BatchNorm2d(12)
    self.srelu = nn.ReLU(inplace=True)
    self.maxpool1 = nn.MaxPool2d(kernel_size=2, stride=2, padding=1)
    self.fr1 = firem(12,6,12)
    self.fr2 = firem(24,6,12)
    self.fr3 = firem(24, 12,24)
    self.fr4 = firem(48,12,24)
    self.maxpool2 = nn.MaxPool2d(kernel_size=2, stride=2, padding=1)
    self.fr5 = firem(48,24,48)
    self.fr6 = firem(96, 24, 48)
    self.fr7 = firem(96,48, 96)
    self.fr8 = firem(128, 48,96)
    self.maxpool3 = nn.MaxPool2d(kernel_size=3, stride=2,padding=1)

  def forward(self, x):
    x = self.sconv1(x)
    x = self.sbn1(x)
    x = self.maxpool1(x)
    x = self.srelu(x)
    x = self.fr1(x)
    x = self.fr2(x)
    x = self.fr3(x)
    y_1 = self.fr4(x)
    #print(y_1.size())
    x1 = self.maxpool2(y_1)
    x1 = self.fr5(x1)
    x1 = self.fr6(x1)
    x1 = self.fr7(x1)
    y_2 = self.maxpool3(x1)
    #y_2 = self.fr8(x)
    return y_1, y_2



class ASPP(nn.Module):
  def __init__(self, in_ch):
    super(ASPP,self).__init__()
    self.squznet_1 = snet(3)
    self.avgpooling = nn.AvgPool2d(kernel_size=(3,3), stride=1, padding=1)
    self.conv1 = nn.Conv2d(192, 8, kernel_size=1, stride=1, bias=False)
    self.bn1 = nn.BatchNorm2d(8)
    self.relu1 =nn.ReLU(inplace=True)
    self.conv2 = nn.Conv2d(192, 8, kernel_size=1, stride=1, bias=False)

    self.dconv1 = nn.Conv2d(192,8, kernel_size=3, dilation=2, padding=2, bias=False)

    self.dconv2 = nn.Conv2d(192,8, kernel_size=3, dilation=4, padding=4, bias=False)


  def forward(self, x):
    #s1 = self.squznet_1(x)
    X_avg = self.avgpooling(x)

    y_1 = self.conv1(X_avg)
    y_1 = self.bn1(y_1)
    y_1 = self.relu1(y_1)

    y_2 = self.conv2(x)
    y_2 = self.bn1(y_2)
    y_2 = self.relu1(y_2)

    y_3 = self.dconv1(x)
    y_3 = self.bn1(y_3)
    y_3 = self.relu1(y_3)

    y_4 = self.dconv2(x)
    y_4 = self.bn1(y_4)
    y_4 = self.relu1(y_4)

    y = torch.cat([y_1, y_2, y_3, y_4],1)
    #print(y.size(), y_1.size(), y_2.size(), y_3.size(), y_4.size())
    return y

#print(summary(ASPP(192), torch.ones(1, 192, 41, 41), show_input=False))

class deeplabv3(nn.Module):
  def __init__ (self, in_cha):
    super(deeplabv3, self).__init__()
    self.squznet = snet(in_cha)
    self.aspp = ASPP(192)
    self.upsmple1 = nn.Upsample(scale_factor=4, mode='bilinear')
    self.conv1 = nn.Conv2d(48, 16, kernel_size=4, stride=1, padding=3, bias=False)
    self.bn1 = nn.BatchNorm2d(16)
    self.relu1 = nn.ReLU(inplace=True)

    self.conv2 = nn.Conv2d(48,16, kernel_size=7, stride=1, padding=1, bias=False)

    self.upsmple2 = nn.Upsample(scale_factor=2, mode='bilinear')
    self.conv3 = nn.Conv2d(16,1, kernel_size=3, stride=1, padding=1, bias=False)

  def forward(self, x):
    x_1 = self.squznet(x)
    c_1 = self.conv1(x_1[0])
    c_1 = self.bn1(c_1)
    c_1 = self.relu1(c_1)


    #print('c_1', c_1.size())
    y_1 = self.aspp(x_1[1])
    #print('y_1',y_1.size())
    y_1 = self.upsmple1(y_1)
    # print('y_1',y_1.size())

    y_2 = torch.cat([y_1,c_1],1)

    y_2 = self.conv2(y_2)
    y_2 = self.bn1(y_2)
    y_2 = self.relu1(y_2)

    y_2 = self.upsmple2(y_2)

    y_2 = self.conv3(y_2)
    return y_2

#print(summary(deeplabv3(3), torch.ones(1, 3, 320, 320), show_input=False))

