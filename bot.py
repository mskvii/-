import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime

load_dotenv()

class GlobalChatBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=os.getenv('APPLICATION_ID'),
            activity=discord.Game(name="グローバルチャット中")
        )
        
        # グローバルチャットデータ
        self.global_channels = set()
        self.server_settings = {}
        self.message_cache = {}
        
    async def setup_hook(self):
        """起動時の初期化処理"""
        print("グローバルチャットボットを初期化中...")
        
        # Cogの読み込み
        await self.load_cogs()
        
        # データ読み込み
        await self.load_data()
        
        print("初期化完了")
    
    async def load_cogs(self):
        """Cogを読み込む"""
        cogs_dir = "cogs"
        
        if not os.path.exists(cogs_dir):
            os.makedirs(cogs_dir)
            return
        
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_path = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_path)
                    print(f"Cogを読み込みました: {cog_path}")
                except Exception as e:
                    print(f"Cogの読み込みに失敗: {cog_path} - {e}")
    
    async def load_data(self):
        """データを読み込む"""
        try:
            with open('data/global_channels.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.global_channels = set(data.get('channels', []))
                self.server_settings = data.get('settings', {})
            print("データを読み込みました")
        except FileNotFoundError:
            print("データファイルがありません。新規作成します")
            await self.save_data()
        except Exception as e:
            print(f"データ読み込みエラー: {e}")
    
    async def save_data(self):
        """データを保存"""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'channels': list(self.global_channels),
                'settings': self.server_settings
            }
            with open('data/global_channels.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"データ保存エラー: {e}")
    
    async def on_ready(self):
        """ボット準備完了時の処理"""
        print(f'{self.user} がログインしました！')
        print(f'サーバー数: {len(self.guilds)}')
        print(f'グローバルチャンネル数: {len(self.global_channels)}')
        
        # スラッシュコマンドを同期
        try:
            synced = await self.tree.sync()
            print(f'スラッシュコマンドを同期しました: {len(synced)}個')
        except Exception as e:
            print(f'スラッシュコマンドの同期に失敗しました: {e}')
    
    async def on_guild_join(self, guild):
        """サーバー参加時の処理"""
        print(f'新しいサーバーに参加しました: {guild.name}')
        
        # デフォルト設定
        self.server_settings[str(guild.id)] = {
            'enabled': False,
            'channel_id': None,
            'filter_enabled': True,
            'auto_translate': False,
            'welcome_message': True
        }
        await self.save_data()
    
    async def on_guild_remove(self, guild):
        """サーバー退出時の処理"""
        print(f'サーバーから退出しました: {guild.name}')
        
        # グローバルチャンネルから削除
        if str(guild.id) in self.server_settings:
            channel_id = self.server_settings[str(guild.id)].get('channel_id')
            if channel_id:
                self.global_channels.discard(channel_id)
            del self.server_settings[str(guild.id)]
            await self.save_data()
    
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        # ボット自身のメッセージは無視
        if message.author == self.user:
            return
        
        # DMは無視
        if not message.guild:
            return
        
        # グローバルチャンネルチェック
        if message.channel.id in self.global_channels:
            await self.handle_global_message(message)
    
    async def handle_global_message(self, message):
        """グローバルメッセージの処理"""
        try:
            # サーバー設定取得
            guild_id = str(message.guild.id)
            settings = self.server_settings.get(guild_id, {})
            
            # 無効化チェック
            if not settings.get('enabled', False):
                return
            
            # フィルタリング
            if settings.get('filter_enabled', True):
                if await self.is_inappropriate(message.content):
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention} 不適切なメッセージは削除されました",
                        delete_after=5
                    )
                    return
            
            # メッセージ作成
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # 送信者情報
            embed.set_author(
                name=f"{message.author.name} ({message.guild.name})",
                icon_url=message.author.display_avatar.url
            )
            
            # サーバー情報
            embed.set_footer(
                text=f"{message.guild.name} | {message.channel.name}"
            )
            
            # 添付ファイル
            if message.attachments:
                attachment = message.attachments[0]
                if attachment.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    embed.set_image(url=attachment.url)
                else:
                    embed.add_field(
                        name="添付ファイル",
                        value=f"[{attachment.filename}]({attachment.url})",
                        inline=False
                    )
            
            # 全グローバルチャンネルに送信
            for channel_id in self.global_channels:
                if channel_id != message.channel.id:
                    try:
                        channel = self.get_channel(channel_id)
                        if channel:
                            await channel.send(embed=embed)
                    except Exception as e:
                        print(f"メッセージ送信エラー (チャンネル {channel_id}): {e}")
        
        except Exception as e:
            print(f"グローバルメッセージ処理エラー: {e}")
    
    async def is_inappropriate(self, content):
        """不適切な内容チェック"""
        # 簡単なフィルタリング（実際はもっと高度なものが必要）
        inappropriate_words = [
            '殺す', '死ね', '自殺', 'テロ', '爆弾',
            'ドラッグ', '麻薬', '違法', 'ハッキング'
        ]
        
        content_lower = content.lower()
        return any(word in content_lower for word in inappropriate_words)

def main():
    """メイン関数"""
    if not os.getenv('DISCORD_TOKEN'):
        print("DISCORD_TOKENが設定されていません")
        return
    
    if not os.getenv('APPLICATION_ID'):
        print("APPLICATION_IDが設定されていません")
        return
    
    bot = GlobalChatBot()
    
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except KeyboardInterrupt:
        print("ボットを停止します")
    except Exception as e:
        print(f"ボット起動エラー: {e}")

if __name__ == "__main__":
    main()
