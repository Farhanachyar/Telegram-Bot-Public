AUTHORIZED_USERS = YOUR USER ID

# Command /restart
@app.on_message(filters.command("restart") & filters.user(AUTHORIZED_USERS))
async def restart_handler(client: Client, message: Message):
    await message.reply_text("🔄 Restarting the bot...")
    
    # Log the restart action with date, time, and user ID
    user_id = message.from_user.id
    timestamp = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")  # Waktu dalam WIB
    
    log_file_path = "restart_log.txt"
    
    with open(log_file_path, "r") as log_file:
        lines = log_file.readlines()
    
    if len(lines) >= 5:
        lines.pop(0)  # Remove the oldest log line
    
    lines.append(f"{timestamp} - User ID: {user_id} initiated restart\n")
    
    with open(log_file_path, "w") as log_file:
        log_file.writelines(lines)
    
    logger.info("Restart initiated by user ID: %s", user_id)
    asyncio.create_task(stop_bot(restart=True))

# Command /restart_log
@app.on_message(filters.command("restart_log") & filters.user(AUTHORIZED_USERS))
async def restart_log_handler(client: Client, message: Message):
    try:
        with open("restart_log.txt", "r") as log_file:
            log_contents = log_file.read()
        
        # Send the log contents to the user
        if log_contents:
            await message.reply_text(f"📜 Restart Log:\n\n{log_contents}")
        else:
            await message.reply_text("📝 The restart log is empty.")
    
    except FileNotFoundError:
        await message.reply_text("⚠️ Restart log file not found.")
    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

async def stop_bot(restart=False):
    global health_check_process, app

    logger.info("Initiating graceful shutdown...")

    # example to stop a task in progress
    if health_check_process and health_check_process.is_alive():
        logger.info("Terminating Flask health check process...")
        health_check_process.terminate()
        health_check_process.join(timeout=5)
        if health_check_process.is_alive():
            logger.warning("Flask process did not terminate in time. Forcing termination.")
            health_check_process.kill()
        logger.info("Flask health check process terminated.")

    logger.info("Stopping Pyrogram client...")
    await app.stop()
    logger.info("Pyrogram client stopped.")

    # Cancel all pending asyncio tasks
    logger.info("Cancelling all pending asyncio tasks...")
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All pending asyncio tasks cancelled.")

    shutdown_event.set()

    logger.info("Graceful shutdown complete.")

    if restart:
        logger.info("Restart flag detected. Restarting the bot...")
        await asyncio.sleep(1) 
        python = sys.executable
        script_path = os.path.abspath(__file__)  # Use absolute path to the current script
        try:
            subprocess.Popen([python, script_path])
            logger.info("Restart command issued. Exiting current process.")
        except Exception as e:
            logger.error(f"Failed to restart the bot: {e}")
    else:
        logger.info("Exiting the bot without restart.")

    os._exit(0)  # Force exit the process
