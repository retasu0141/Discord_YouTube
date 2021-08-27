import discord
import asyncio
import youtube_dl
import ffmpeg
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
TOKEN = 'xxxx'
client = discord.Client()
@client.event
async def on_message(message):
    if message.author.bot:
        return
    elif message.content == "!join":
        if message.author.voice is None:
            await message.channel.send("ボイスチャンネルに接続してください。")
            return
        await message.author.voice.channel.connect()
        await message.channel.send("接続しました。")
    elif message.content == "!leave":
        if message.guild.voice_client is None:
            await message.channel.send("ボイスチャンネルに接続していません!")
            return
        await message.guild.voice_client.disconnect()
        await message.channel.send("切断しました。")
    elif message.content.startswith("!play "):
        if message.guild.voice_client is None:
            await message.channel.send("接続していません。")
            return
        if message.guild.voice_client.is_playing():
            await message.channel.send("再生中です。")
            return
        url = message.content[6:]

        # 参考記事 : https://qiita.com/ko_cha/items/3aeb075a83823eaa48d6

        #player = await YTDLSource.from_url(url, loop=client.loop)
        #↑ loop=client.loop　の後に　stream=True　を追加

        #await message.guild.voice_client.play(player)
        #どうやらそもそもawaitはここでは必要ないらしい
        #上の記事を参考に(というかほぼコピペ)で after=lambda e: print('Player error: %s' % e) if e else None を追加

        player = await YTDLSource.from_url(url, loop=client.loop,stream=True)
        message.guild.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        # ^ここでTypeError: object NoneType can't be used in 'await' expressionがでる
        #多分出なくなって正常に動くようになったと思います！
        await message.channel.send('{} を再生します。'.format(player.title))
    elif message.content == "!pause":
        if message.guild.voice_client is None:
            await message.channel.send("接続していません。")
            return
        message.guild.voice_client.pause()
        await message.channel.send('Paused.')
    elif message.content == "!stop":
        if message.guild.voice_client is None:
            await message.channel.send("ERROR!_接続していません。")
            return
        if not message.guild.voice_client.is_playing():
            await message.channel.send("ERROR!_再生していません。")
            return
        message.guild.voice_client.stop()
        await message.channel.send('Stopped.')
client.run(TOKEN)
