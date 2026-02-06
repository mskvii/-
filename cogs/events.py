import discord
from discord.ext import commands
import asyncio
from datetime import datetime

class Events(commands.Cog):
    """イベント処理"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """メンバー参加時の処理"""
        guild_id = str(member.guild.id)
        
        if guild_id not in self.bot.server_settings:
            return
        
        settings = self.bot.server_settings[guild_id]
        
        if not settings.get('welcome_message', True):
            return
        
        channel = self.bot.get_channel(settings['channel_id'])
        if not channel:
            return
        
        embed = discord.Embed(
            title='👋 新しいメンバーが参加しました！',
            description=f'{member.mention} がサーバーに参加しました',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"ウェルカムメッセージ送信エラー: {e}")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """メッセージ編集時の処理"""
        # グローバルチャンネルチェック
        if after.channel.id not in self.bot.global_channels:
            return
        
        # 内容が同じなら無視
        if before.content == after.content:
            return
        
        # 編集通知
        embed = discord.Embed(
            title='✏️ メッセージが編集されました',
            description=f'**元のメッセージ:** {before.content}\n**編集後:** {after.content}',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f'{after.author.name} ({after.guild.name})',
            icon_url=after.author.display_avatar.url
        )
        
        embed.set_footer(text=f'{after.guild.name} | {after.channel.name}')
        
        # 他のグローバルチャンネルに送信
        for channel_id in self.bot.global_channels:
            if channel_id != after.channel.id:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                except Exception as e:
                    print(f"編集通知送信エラー: {e}")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """メッセージ削除時の処理"""
        # グローバルチャンネルチェック
        if message.channel.id not in self.bot.global_channels:
            return
        
        # ボットのメッセージは無視
        if message.author == self.bot.user:
            return
        
        # 削除通知
        embed = discord.Embed(
            title='🗑️ メッセージが削除されました',
            description=message.content or '*（コンテンツなし）*',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f'{message.author.name} ({message.guild.name})',
            icon_url=message.author.display_avatar.url
        )
        
        embed.set_footer(text=f'{message.guild.name} | {message.channel.name}')
        
        # 添付ファイルがあった場合
        if message.attachments:
            embed.add_field(
                name='添付ファイル',
                value='\n'.join([f'• {a.filename}' for a in message.attachments]),
                inline=False
            )
        
        # 他のグローバルチャンネルに送信
        for channel_id in self.bot.global_channels:
            if channel_id != message.channel.id:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                except Exception as e:
                    print(f"削除通知送信エラー: {e}")

async def setup(bot):
    await bot.add_cog(Events(bot))
