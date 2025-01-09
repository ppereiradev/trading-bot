# Trading Bot Setup

1. Add your API key, secret key, asset (e.g., USDT), and symbol (e.g., BTCUSDT) to the respective variables in the `.env.sample` file, then rename this file to `.env`.

2. Execute the command:
```bash
docker compose up -y
```

3. After the container is up, execute:
```bash
docker container exec -it trading-bot bash
```

4. Inside the container, run:
```bash
python main.py
```

5. Keep watching the terminal for logs.

6. Open your browser and go to `localhost:8050` to view the chart. The chart will be updated every 150 seconds.

7. The trading profit will be saved in lucros.txt and will also be displayed in the terminal.
