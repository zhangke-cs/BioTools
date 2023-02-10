# UDP SERVER FOLDER

这是一个用于程序运行信息记录功能的UDP Socket服务器，基于整个系统中有UDP服务器、应用程序和MySQL服务器。

## 服务器功能：

1. 作为应用程序认证服务器，通过识别系统机器码和IP地址实现。
2. 作为应用程序运行信息记录服务器，收集应用程序运行信息并记录到MySQL数据库。

## 服务器实现：

1. socketserver 实现服务器框架。
2. pickle 实现信息的序列化。
3. pymysql 实现数据库连接。

首先，在服务端启动server.py到后台；然后，应用程序在运行时调用client.py的verify方法向服务端发送运行认证信息，服务端经过认证后返回确认信息应用程序继续运行；最后，应用程序在即将结束时调用client.py的record方法收集信息并将信息发送到服务端。