from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Static, DataTable, Header, Footer
from textual.containers import Vertical, Horizontal
import asyncio
import aiohttp

class VDSApp(App):
    TITLE = "VDS Ping & Speed Tester"
    BINDINGS = [("q", "quit", "Exit")]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Input(id="input", placeholder="Введите IP или домены через пробел"),
            Button("🚀 Тестировать", id="test_button"),
            DataTable(id="results_table", zebra_stripes=True),
            Static("⏳ Ожидание теста...", id="status")
        )
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        input_widget = self.query_one("#input", Input)
        results_table = self.query_one("#results_table", DataTable)
        status_widget = self.query_one("#status", Static)
        
        raw_text = input_widget.value.strip()
        hosts = raw_text.split()
        if not hosts:
            status_widget.update("❌ Введите хотя бы один IP или домен!")
            return

        status_widget.update("🔄 Тестирование... Подождите...")
        results_table.clear()
        results_table.add_columns("Хост", "Пинг (ms)", "Скорость (MB/s)")
        
        results = await self.test_hosts(hosts)
        sorted_results = sorted(results, key=lambda x: x[1])
        
        for host, ping, speed in sorted_results:
            results_table.add_row(host, str(ping), str(speed))
        
        if sorted_results:
            best = sorted_results[0]
            status_widget.update(f"🏆 Лучшая локация: {best[0]} | Пинг: {best[1]} ms | Скорость: {best[2]} MB/s")
        else:
            status_widget.update("❌ Не удалось проверить сервера.")
    
    async def test_hosts(self, hosts):
        results = []
        for host in hosts:
            ping = await self.ping_host(host)
            speed = await self.speed_test(host)
            if ping is not None and speed is not None:
                results.append((host, ping, speed))
        return results

    async def ping_host(self, host):
        cmd = ["ping", "-c", "3", "-q", host]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()
            if "min/avg/max" in output:
                avg_ping = float(output.split("/")[4])
                return round(avg_ping, 2)
        except Exception:
            return None
        return None

    async def speed_test(self, host):
        url = f"http://{host}/1MB.test"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    start = asyncio.get_event_loop().time()
                    await response.read()
                    end = asyncio.get_event_loop().time()
                    speed = 1 / (end - start)  # MB/s
                    return round(speed, 2)
        except Exception:
            return None
        return None

if __name__ == "__main__":
    VDSApp().run()

