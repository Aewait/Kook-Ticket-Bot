# encoding: utf-8:
import json
import requests
import aiohttp
import time

from khl import Bot, Message, EventTypes, Event,Client,PublicMessage
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from khl.command import Rule

# 新建机器人，token 就是机器人的身份凭证
with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config['token'])

# kook api的头链接，请不要修改
kook_base="https://www.kookapp.cn"
Botoken = config['token']
headers={f'Authorization': f"Bot {Botoken}"}

#将获取当前时间封装成函数方便使用
def GetTime():  
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

#记录开机时间
start_time = GetTime()

# 在控制台打印msg内容，用作日志
def logging(msg: Message):
    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}")

def logging2(e: Event):
    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{now_time}] Event:{e.body}")

# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name='hello')
async def world(msg: Message):
    logging(msg)
    await msg.reply('world!')
    
    
#####################################机器人动态#########################################
 
from status import status_active_game,status_active_music,status_delete

# 开始打游戏
@bot.command()
async def gaming(msg: Message,game:int):
    logging(msg)
    #await bot.client.update_playing_game(3,1)# 英雄联盟
    if game == 1:    
        ret = await status_active_game(464053) # 人间地狱
        await msg.reply(f"{ret['message']}，Bot上号人间地狱啦！")
    elif game == 2:
        ret = await status_active_game(3)      # 英雄联盟
        await msg.reply(f"{ret['message']}，Bot上号LOL啦！")
    elif game == 3:
        ret = await status_active_game(23)     # CSGO
        await msg.reply(f"{ret['message']}，Bot上号CSGO啦！")

# 开始听歌
@bot.command()
async def singing(msg: Message,music:str,singer:str):
    logging(msg)
    ret = await status_active_music(music,singer)
    await msg.reply(f"{ret['message']}，Bot开始听歌啦！")
    
# 停止打游戏1/听歌2
@bot.command(name='sleep')
async def sleeping(msg: Message,d:int):
    logging(msg)
    ret = await status_delete(d)
    if d ==1:
        await msg.reply(f"{ret['message']}，Bot下号休息啦!")
    elif d==2:
        await msg.reply(f"{ret['message']}，Bot摘下了耳机~")

################################以下是给ticket功能的内容########################################

# 从文件中读取频道和分组id
with open('./config/TicketConf.json', 'r', encoding='utf-8') as f1:
    TKconf = json.load(f1)

# ticket系统,发送卡片消息
@bot.command()
async def ticket(msg: Message):
    logging(msg)
    global TKconf
    if msg.author_id in TKconf["admin_user"]:
        ch_id = msg.ctx.channel.id #当前所处的频道id
        # 发送消息
        send_msg = await msg.ctx.channel.send(
                        CardMessage(
                            Card(Module.Section(
                                    '请点击右侧按钮发起ticket',
                                    Element.Button('发起ticket',Types.Click.RETURN_VAL)))))
        if ch_id not in TKconf["channel_id"]: #如果不在    
            # 发送完毕消息，并将该频道插入此目录
            TKconf["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
            print(f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} MsgID:{send_msg['msg_id']}")
        else:
            old_msg = TKconf["channel_id"][ch_id] #记录旧消息的id输出到日志
            TKconf["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
            print(f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} New_MsgID:{send_msg['msg_id']} Old:{old_msg}")

        # 保存到文件
        with open("./config/TicketConf.json", 'w', encoding='utf-8') as fw2:
            json.dump(TKconf, fw2, indent=2, sort_keys=True, ensure_ascii=False)
    else:
        await msg.reply(f"您没有权限执行本命令！")

# 监看工单系统
# 相关api文档 https://developer.kaiheila.cn/doc/http/channel#%E5%88%9B%E5%BB%BA%E9%A2%91%E9%81%93
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_ticket(b: Bot, e: Event):
    # 判断是否为ticket申请频道的id（文字频道id）
    global TKconf
    if e.body['target_id'] in TKconf["channel_id"]:
        logging2(e)
        global kook_base,headers
        url1=kook_base+"/api/v3/channel/create"# 创建频道
        params1 = {"guild_id": e.body['guild_id'] ,"parent_id":TKconf["category_id"],"name":e.body['user_info']['username']}
        async with aiohttp.ClientSession() as session:
            async with session.post(url1, data=params1,headers=headers) as response:
                    ret1=json.loads(await response.text())
                    #print(ret1["data"]["id"])

        url2=kook_base+"/api/v3/channel-role/create"#创建角色权限
        params2 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id']}
        async with aiohttp.ClientSession() as session:
            async with session.post(url2, data=params2,headers=headers) as response:
                    ret2=json.loads(await response.text())
                    #print(f"ret2: {ret2}")
        
        # 服务器角色权限值见 https://developer.kaiheila.cn/doc/http/guild-role
        url3=kook_base+"/api/v3/channel-role/update"#设置角色权限
        params3 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id'],"allow":2048}
        async with aiohttp.ClientSession() as session:
            async with session.post(url3, data=params3,headers=headers) as response:
                    ret3=json.loads(await response.text())
                    #print(f"ret3: {ret3}")
        
        # 管理员角色id
        text = f"(met){e.body['user_id']}(met) 发起了帮助，请等待管理猿的回复\n"
        for roles_id in TKconf["admin_role"]:
            text+=f"(rol){roles_id}(rol) "
        text+="\n"
        
        cm = CardMessage()# 这里需要修改卡片消息中处理本事件的管理员角色id，(rol)角色id(rol)
        c1 = Card(Module.Section(Element.Text(text,Types.Text.KMD)))
        c1.append(Module.Section('帮助结束后，请点击下方“关闭”按钮关闭该ticket频道\n'))
        c1.append(Module.ActionGroup(Element.Button('关闭', Types.Click.RETURN_VAL,theme=Types.Theme.DANGER)))
        cm.append(c1)
        channel = await b.fetch_public_channel(ret1["data"]["id"]) 
        sent = await bot.client.send(channel,cm)
        return sent
    else:
        return

# 监看关闭情况
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_close(b: Bot, e: Event):
    # 避免与tiket申请按钮冲突（文字频道id）
    if e.body['target_id'] in TKconf["channel_id"]:
        return 
    
    logging2(e)
    global kook_base,headers
    url1=kook_base+"/api/v3/channel/view"#获取频道的信息
    params1 = {"target_id": e.body['target_id']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url1, data=params1,headers=headers) as response:
                ret1=json.loads(await response.text())
    #判断发生点击事件的频道是否在预定分组下，如果不是就不进行操作
    if ret1['data']['parent_id'] != TKconf["category_id"]:
        return 

    url2=kook_base+'/api/v3/channel/delete'#删除频道
    params2 = {"channel_id": e.body['target_id']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url2, data=params2,headers=headers) as response:
                ret2=json.loads(await response.text())
                #print(ret2)
    
################################以下是给用户上色功能的内容########################################

# 22.12.12 这部分写的很烂，等待我重写！新的版本在kook-valorant-bot中有

# 设置自动上色event的服务器id和消息id
Guild_ID = '1573724356603748'
Msg_ID_1 = '0a4b9403-de0b-494e-b216-3d1dbe957d0f'
Msg_ID_2 = '5d92f952-15c1-46a4-b370-41a9cf739e50'
Msg_ID_3 = 'd4dbb164-bd80-469b-9473-8285a9c91e0d'

# 用于记录使用表情回应获取ID颜色的用户
def save_userid_color(userid:str,d:int,emoji:str):
    flag=0
    if d ==1:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_1.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_1.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag

    elif d == 2:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_2.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_2.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag

    elif d == 3:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_3.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_3.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag
     

# 在不修改代码的前提下设置上色功能的服务器和监听消息
@bot.command()
async def Set_GM(msg: Message,d:int,Card_Msg_id:str):
    logging(msg)
    global Guild_ID,Msg_ID_1,Msg_ID_2,Msg_ID_3 #需要声明全局变量
    Guild_ID = msg.ctx.guild.id
    if d == 1:
        Msg_ID_1 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息1更新为 {Msg_ID_1}\n')
    elif d == 2:
        Msg_ID_2 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息2更新为 {Msg_ID_2}\n')
    elif d == 3:
        Msg_ID_3 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息3更新为 {Msg_ID_3}\n')


# 判断消息的emoji回应，并给予不同角色
@bot.on_event(EventTypes.ADDED_REACTION)
async def update_reminder(b: Bot, event: Event):
    g = await b.fetch_guild(Guild_ID)# 填入服务器id
    logging2(event)#事件日志

    channel = await b.fetch_public_channel(event.body['channel_id']) #获取事件频道
    s = await b.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
    # 判断用户回复的emoji是否合法
    emoji=event.body["emoji"]['id']
 
    # 第一个消息
    if event.body['msg_id'] == Msg_ID_1:  #将msg_id和event.body msg_id进行对比，确认是我们要的那一条消息的表情回应
        flag=0
        with open("./config/emoji1.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 1, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`游戏角色`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])
    
    # 第二个消息
    elif event.body['msg_id'] == Msg_ID_2:
        # channel = await b.fetch_public_channel(event.body['channel_id']) #获取事件频道
        # s = await b.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
        # # 判断用户回复的emoji是否合法
        # emoji=event.body["emoji"]['id']
        flag=0
        with open("./config/emoji2.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 2, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`休闲游戏`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])
    
    # 第三个消息
    elif event.body['msg_id'] == Msg_ID_3:
        flag=0
        with open("./config/emoji3.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 3, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`社会身份`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])

# 开机的时候打印一次时间，记录重启时间
print(f"Start at: [%s]" % start_time)

# 凭证传好了、机器人新建好了、指令也注册完了
# 接下来就是运行我们的机器人了，bot.run() 就是机器人的起跑线
bot.run()