import discord
from discord.ext import commands
from discord import ui
import asyncio

class GlobalSetupModal(ui.Modal, title='グローバルチャット設定'):
    def __init__(self):
        super().__init__()
        
    channel_select = ui.TextInput(
        label='グローバルチャンネル名',
        placeholder='グローバルチャットに使用するチャンネル名',
        style=discord.TextStyle.short,
        required=True
    )
    
    welcome_msg = ui.TextInput(
        label='ウェルカムメッセージ',
        placeholder='グローバルチャットへようこそ！',
        style=discord.TextStyle.short,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # チャンネル検索
        channel = discord.utils.get(
            interaction.guild.text_channels,
            name=self.channel_select.value
        )
        
        if not channel:
            await interaction.response.send_message(
                f'チャンネル「{self.channel_select.value}」が見つかりません',
                ephemeral=True
            )
            return
        
        # ボットに権限チェック
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                '指定されたチャンネルにメッセージを送信する権限がありません',
                ephemeral=True
            )
            return
        
        # 設定保存
        bot = interaction.client
        guild_id = str(interaction.guild.id)
        
        bot.server_settings[guild_id] = {
            'enabled': True,
            'channel_id': channel.id,
            'filter_enabled': True,
            'auto_translate': False,
            'welcome_message': self.welcome_msg.value or 'グローバルチャットへようこそ！'
        }
        
        bot.global_channels.add(channel.id)
        await bot.save_data()
        
        # ウェルカムメッセージ送信
        if self.welcome_msg.value:
            embed = discord.Embed(
                title='🌍 グローバルチャット開始！',
                description=self.welcome_msg.value,
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
        
        await interaction.response.send_message(
            f'グローバルチャットを「{channel.name}」に設定しました！',
            ephemeral=True
        )

class Admin(commands.Cog):
    """管理者用コマンド"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='global_setup', description='グローバルチャットを設定します')
    @commands.has_permissions(administrator=True)
    async def global_setup(self, ctx: commands.Context):
        """グローバルチャット設定"""
        modal = GlobalSetupModal()
        if ctx.interaction:
            await ctx.interaction.response.send_modal(modal)
        else:
            # プレフィックスコマンド用の処理
            await ctx.send("モーダルフォームはスラッシュコマンド `/global_setup` を使用してください", ephemeral=True)
    
    @commands.hybrid_command(name='global_toggle', description='グローバルチャットの有効/無効を切り替えます')
    @commands.has_permissions(administrator=True)
    async def global_toggle(self, ctx: commands.Context):
        """グローバルチャットの有効/無効切り替え"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.server_settings:
            await ctx.send('まず `/global_setup` で設定してください', ephemeral=True)
            return
        
        settings = self.bot.server_settings[guild_id]
        settings['enabled'] = not settings['enabled']
        
        if settings['enabled']:
            channel_id = settings['channel_id']
            if channel_id:
                self.bot.global_channels.add(channel_id)
        else:
            channel_id = settings['channel_id']
            if channel_id:
                self.bot.global_channels.discard(channel_id)
        
        await self.bot.save_data()
        
        status = '有効' if settings['enabled'] else '無効'
        await ctx.send(f'グローバルチャットを{status}にしました', ephemeral=True)
    
    @commands.hybrid_command(name='global_filter', description='フィルタリング設定を変更します')
    @commands.has_permissions(administrator=True)
    async def global_filter(self, ctx: commands.Context, enabled: bool):
        """フィルタリング設定"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.server_settings:
            await ctx.send('まず `/global_setup` で設定してください', ephemeral=True)
            return
        
        self.bot.server_settings[guild_id]['filter_enabled'] = enabled
        await self.bot.save_data()
        
        status = '有効' if enabled else '無効'
        await ctx.send(f'コンテンツフィルターを{status}にしました', ephemeral=True)
    
    @commands.hybrid_command(name='global_info', description='グローバルチャットの情報を表示します')
    async def global_info(self, ctx: commands.Context):
        """グローバルチャット情報表示"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.server_settings:
            await ctx.send('このサーバーではグローバルチャットが設定されていません', ephemeral=True)
            return
        
        settings = self.bot.server_settings[guild_id]
        channel = self.bot.get_channel(settings['channel_id'])
        
        embed = discord.Embed(
            title='🌍 グローバルチャット情報',
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name='ステータス',
            value='🟢 有効' if settings['enabled'] else '🔴 無効',
            inline=True
        )
        
        embed.add_field(
            name='チャンネル',
            value=channel.mention if channel else '不明',
            inline=True
        )
        
        embed.add_field(
            name='フィルター',
            value='🟢 有効' if settings['filter_enabled'] else '🔴 無効',
            inline=True
        )
        
        embed.add_field(
            name='参加サーバー数',
            value=str(len(self.bot.global_channels)),
            inline=True
        )
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='global_servers', description='参加サーバー一覧を表示します')
    async def global_servers(self, ctx: commands.Context):
        """参加サーバー一覧"""
        servers = []
        
        for channel_id in self.bot.global_channels:
            channel = self.bot.get_channel(channel_id)
            if channel and channel.guild:
                servers.append(f"• {channel.guild.name}")
        
        if not servers:
            await ctx.send('参加サーバーがありません', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='🌍 参加サーバー一覧',
            description='\n'.join(servers),
            color=discord.Color.green()
        )
        
        embed.set_footer(text=f'合計 {len(servers)} サーバー')
        
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
