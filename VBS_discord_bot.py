import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import re
from discord import opus

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']

def load_opus_lib(opus_libs=OPUS_LIBS):
if opus.is_loaded():
    return True

for opus_lib in opus_libs:
    try:
        opus.load_opus(opus_lib)
        return
    except OSError:
        pass

# Client = discord.Client()
prefix = "!"
bot = commands.Bot(command_prefix=prefix)
flag = 0
ban = ""


def get_song(song):
    res = requests.get('https://www.youtube.com/results?search_query={}'.format(song), verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    text = soup.select(".yt-uix-tile-link")[0]
    return "https://www.youtube.com{}".format(text['href'])


def get_page_number(content):
    start_index = content.find('index')
    end_index = content.find('.html')
    page_number = content[start_index + 5: end_index]
    return int(page_number) + 1


def ptt_beauty():
    rs = requests.session()
    res = rs.get('https://www.ptt.cc/bbs/Beauty/index.html', verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('.btn.wide')[1]['href']
    start_page = get_page_number(all_page_url)
    page_term = 2  # crawler count
    push_rate = 10  # 推文
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -1):
        page_url = 'https://www.ptt.cc/bbs/Beauty/index{}.html'.format(page)
        index_list.append(page_url)

    # 抓取 文章標題 網址 推文數
    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
        if res.status_code != 200:
            index_list.append(index)
        else:
            article_list = craw_page(res, push_rate)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                             article.get('url', None))
        content += data
    return content


def craw_page(res, push_rate):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    for r_ent in soup_.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']
            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                rate = r_ent.find(class_="nrec").text
                url = 'https://www.ptt.cc' + link
                if rate:
                    rate = 100 if rate.startswith('爆') else rate
                    rate = -1 * int(rate[1]) if rate.startswith('X') else rate
                else:
                    rate = 0
                # 比對推文數
                if int(rate) >= push_rate:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            # print('crawPage function error:',r_ent.find(class_="title").text.strip())
            #print('本文已被刪除', e)
            pass
    return article_seq


def crawl_page_gossiping(res):
    soup = BeautifulSoup(res.text, 'html.parser')
    article_gossiping_seq = []
    for r_ent in soup.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']

            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                url_link = 'https://www.ptt.cc' + link
                article_gossiping_seq.append({
                    'url_link': url_link,
                    'title': title
                })

        except Exception as e:
            # print u'crawPage function error:',r_ent.find(class_="title").text.strip()
            # print('本文已被刪除')
            print('delete', e)
    return article_gossiping_seq


@bot.event
async def on_ready():
    global VC, player
    print("Bot Activating!")
    print("Name: {}".format(bot.user.name))
    print("ID: {}".format(bot.user.id))

    for index, channel in enumerate(bot.get_all_channels()):
        if index == 6:
            # print(channel.name)
            VC = await bot.join_voice_channel(channel)
    player = await VC.create_ytdl_player('https://www.youtube.com/watch?v=_nI-Pm_oiGA')
    player.stop()
    await VC.disconnect()
    print("Done!")


@bot.command(pass_context=True)
async def hello(context):
    await bot.send_message(context.message.author, "你好啊~ {}".format(context.message.author))


@bot.command(pass_context=True)
async def invite(context):
    invite = await bot.create_invite(destination=context.message.channel)
    await bot.send_message(context.message.author, "Your invite URL is {}".format(invite.url))
    await bot.delete_message(context.message)


@bot.command(pass_context=True)
async def GGININDER(context):
    await bot.send_message(context.message.author, ptt_beauty())


@bot.command(pass_context=True)
async def YT(context):
    await bot.send_message(context.message.author, "discord 本身有BUG 音樂可能隨機中斷停止播放")
    global VC, player
    if not(player.is_playing()):
        try:
            VC = await bot.join_voice_channel(context.message.author.voice_channel)
        except:
            pass
        url = get_song(re.split(r' ', context.message.content)[1])
        player = await VC.create_ytdl_player(url)
        player.start()
        while not(player.is_done()):
            pass
        await VC.disconnect()
    else:
        await bot.send_message(context.message.author, "請稍等喔~已經有東西再播放了~")
        await bot.delete_message(context.message)

        # despacito # https://www.youtube.com/watch?v=_nI-Pm_oiGA


@bot.command(pass_context=True)
async def TTS(context):
    await bot.send_message(context.message.channel, re.split(r' ', context.message.content)[-1], tts=True)


@bot.listen()
async def on_member_join(member):
    await bot.send_message(member, "觀迎來到VBS for gaming頻道~ 語音頻道有分類喔~")
    await bot.say("成員{}來到這個頻道囉~ 快跟他一起遊玩~".format(member.name))

if __name__ == '__main__':
    bot.run("NDMyMjQwMjUzMTg1NTU2NTAx.DaqcDQ.m1JlMSoALr5dw4OeKlrTVaVGfDE")
