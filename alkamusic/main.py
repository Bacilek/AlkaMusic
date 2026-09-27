from alkamusic.install import ensure_installed


def main():
    if ensure_installed():
        return
    from alkamusic.ui import App

    App().mainloop()


if __name__ == "__main__":
    main()
