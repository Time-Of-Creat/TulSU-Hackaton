from source.application import Application


if __name__ == "__main__":
    app = Application()
    app.run() # Эта функция должна запускать оконное приложение и логику симуляции одновременно (по идее в два потока)
