# gh 8位继电器版,串口测温，2路测温
更新clone下来的代码 git pull，视频要手动

# gh
要装的程序

sudo apt-get update
sudo apt-get install -y ttf-wqy-zenhei samba-common-bin samba python3-rpi.gpio
sudo pip3 install pexpect aiohttp==0.22.5 aiohttp_jinja2

禁用屏保和休眠
sudo leafpad /etc/lightdm/lightdm.conf 行xserver-command=X -s o -dpms

samba文件共享
sudo leafpad /etc/samba/smb.conf  [homes]段
browseable = yes

read only = no
create mask = 0755
directory mask = 0755

增加samba用户
sudo smbpasswd -a pi 输入两次密码，重启

开机运行Python脚本
sudo pcmanfm 复制desktop文件到 /home/pi/.config/autostart

设定有线固定IP，设置中文，设置时区，设置背景,关闭设置里接口，开启IIC
可以直接在图形界面设置固定IP

# 备用
HDMI输出声音
$ sudo leafpad /boot/config.txt 里面设置HDMI_DRIVER=2,参数是：-o hdmi


看网上的教程都是用hostapd和isc-dhcp-server来搞，对着教程敲了一大堆命令折腾了三个小时无果，看网上都是针对的pi2用usb网卡整的，而pi3自带wifi，可能pi3不适用吧。于是网上各种搜，最后在github上发现神器create_ap，好家伙，看着安装方法好简单。废话不多说，下面上干货：

1.git clone https://github.com/oblique/create_ap.git

2.cd create_ap

3.sudo make install就这样安装好了

4.接下来安装依赖库，记得软件源换成 阿里云
sudo apt-get update
sudo apt-get install util-linux procps hostapd iproute2 iw haveged dnsmasq

5.就这么简单几个命令就能安装好全部环境

6.接下来保证你的网线插在pi3上并且能上网就行了。输入下面的命令启动无线AP：

sudo create_ap --no-virt wlan0 eth0 热点名 密码

接下来就去打开手机wifi看看有没有上面命令中设置的热点名吧，有的话输入密码即可连接上，enjoy your PI3 wireless AP！

可以把上述的启动命令添加到/etc/rc.local就可以开机自启动了。

是不是很简单，这个AP的局域网无线传输速度居然比我原来那个老AP还快一倍，也算是惊喜了，从此我的树莓派3又增加了一个功能。

ifup、ifdown = ifconfig eth0  up/down

sudo apt-get update
sudo apt-get install -y util-linux procps hostapd iproute2 iw haveged dnsmasq
git clone https://github.com/oblique/create_ap.git
cd create_ap
sudo make install
sudo ifdown wlan0
sudo create_ap --no-virt -n -g 192.168.11.22 wlan0 gh_up 66341703

# 在线升级
上传 gpmb.zip 到 192.168.11.22:9002/upgrade 
热点名gh_up 热点密码66341703
