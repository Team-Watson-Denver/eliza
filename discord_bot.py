import discord
from discord.ext import commands
import json
import openai
import os
from dotenv import load_dotenv
import re

# Load environment variables FIRST
load_dotenv()

# Add these debug lines
print("Environment variables loaded:")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"DISCORD_BOT_TOKEN existsp: {bool(os.getenv('DISCORD_BOT_TOKEN'))}")

def resolve_env_vars(config):
    """Recursively resolve environment variables in the config."""
    if isinstance(config, dict):
        return {k: resolve_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_env_vars(i) for i in config]
    elif isinstance(config, str):
        match = re.match(r'\${env:([^}]+)}', config)
        if match:
            env_var = match.group(1)
            return os.getenv(env_var)
    return config

# Load the character configuration
with open('characters/EugeneFama.character.json', 'r') as f:
    character_config = json.load(f)
    character_config = resolve_env_vars(character_config)

# Add debug line to see what we got
print("\nResolved secrets:")
print(character_config['settings']['secrets'])

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configure OpenAI
openai.api_key = character_config['settings']['secrets']['OPENAI_API_KEY']

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return

    # Only respond in channels the bot is mentioned in
    if bot.user not in message.mentions:
        return

    try:
        # Create the system message combining character details
        system_msg = (
            f"{character_config['system']}\n\n"
            f"Character Bio: {' '.join(character_config['bio'])}\n"
            f"Style: {' '.join(character_config['style']['chat'])}"
        )
        
        # Get the user's message without the bot mention
        user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # Create the chat completion
        response = openai.ChatCompletion.create(
            model=character_config['settings']['model'],
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_message}
            ]
        )

        # Send the response
        await message.channel.send(response.choices[0].message.content)

    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("Sorry, I encountered an error!")

# Run the bot
bot.run(character_config['settings']['secrets']['DISCORD_BOT_TOKEN']) 