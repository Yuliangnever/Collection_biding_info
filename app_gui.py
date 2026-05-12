from __future__ import annotations

import csv
import queue
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.config_loader import load_settings
from src.pipeline import TenderPipeline
from src.topic_utils import DEFAULT_TOPICS, parse_topics, settings_with_topics


class TenderMonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("招标信息监控工具")
        self.geometry("980x720")
        self.minsize(860, 600)

        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.last_items: list[dict[str, object]] = []
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None

        self._build_ui()
        self.after(200, self._drain_messages)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(root, text="搜索条件", padding=10)
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="关键词").grid(row=0, column=0, sticky=tk.W)
        self.keyword_var = tk.StringVar(value=" ".join(DEFAULT_TOPICS))
        keyword_entry = ttk.Entry(input_frame, textvariable=self.keyword_var)
        keyword_entry.grid(row=0, column=1, sticky=tk.EW, padx=8)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="自动运行间隔（分钟）").grid(
            row=0, column=2, sticky=tk.W, padx=(12, 0)
        )
        self.interval_var = tk.IntVar(value=30)
        interval_spin = ttk.Spinbox(
            input_frame,
            from_=1,
            to=1440,
            textvariable=self.interval_var,
            width=8,
        )
        interval_spin.grid(row=0, column=3, sticky=tk.W, padx=8)

        hint = (
            "不填写关键词时默认搜索："
            + "、".join(DEFAULT_TOPICS)
            + "。多个关键词可用空格、逗号或顿号分隔。"
        )
        ttk.Label(input_frame, text=hint).grid(
            row=1, column=0, columnspan=4, sticky=tk.W, pady=(8, 0)
        )

        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="获取今日招标信息",
            command=self.fetch_today,
        ).pack(side=tk.LEFT)
        ttk.Button(
            button_frame,
            text="导出 CSV",
            command=self.export_csv,
        ).pack(side=tk.LEFT, padx=8)
        ttk.Button(
            button_frame,
            text="开始自动运行并推送",
            command=self.start_auto_run,
        ).pack(side=tk.LEFT, padx=8)
        ttk.Button(
            button_frame,
            text="停止自动运行",
            command=self.stop_auto_run,
        ).pack(side=tk.LEFT)
        ttk.Button(
            button_frame,
            text="清空显示",
            command=lambda: self.output.delete("1.0", tk.END),
        ).pack(side=tk.RIGHT)

        output_frame = ttk.LabelFrame(root, text="运行结果", padding=8)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output = tk.Text(output_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(output_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _topics(self) -> list[str]:
        return parse_topics(self.keyword_var.get())

    def _pipeline(self, topics: list[str]) -> TenderPipeline:
        settings = settings_with_topics(load_settings(), topics)
        return TenderPipeline(settings)

    def _log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.put(("log", f"[{timestamp}] {text}\n"))

    def _append_result(self, text: str) -> None:
        self.messages.put(("result", text))

    def _drain_messages(self) -> None:
        while True:
            try:
                _, message = self.messages.get_nowait()
            except queue.Empty:
                break
            self.output.insert(tk.END, message)
            self.output.see(tk.END)
        self.after(200, self._drain_messages)

    def fetch_today(self) -> None:
        topics = self._topics()
        self._log(f"开始获取今日招标信息，关键词：{'、'.join(topics)}")

        def worker() -> None:
            try:
                result = self._pipeline(topics).preview_today(topics)
                self.last_items = list(result["items"])
                summary = (
                    f"今日招标信息：日期={result['date']}，"
                    f"关键词={','.join(topics)}，"
                    f"抓取到={result['crawled']}，新增入库={result['inserted']}，"
                    "不会推送企业微信\n"
                )
                self._append_result("\n" + summary)
                messages = list(result["messages"])
                if not messages:
                    self._append_result("没有找到符合条件的今日招标信息。\n")
                for index, message in enumerate(messages, start=1):
                    self._append_result(
                        "\n" + "=" * 80 + f"\n消息 {index}\n" + "=" * 80 + "\n"
                    )
                    self._append_result(message + "\n")
                self._log("今日招标信息获取完成")
            except Exception as exc:
                self._log(f"获取失败：{exc}")

        threading.Thread(target=worker, daemon=True).start()

    def start_auto_run(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("提示", "自动运行已经启动。")
            return

        topics = self._topics()
        interval_minutes = max(int(self.interval_var.get()), 1)
        self.stop_event.clear()
        self._log(
            f"开始自动运行，间隔 {interval_minutes} 分钟，关键词：{'、'.join(topics)}"
        )

        def worker() -> None:
            while not self.stop_event.is_set():
                try:
                    result = self._pipeline(topics).notify_today_topics(
                        topics,
                        limit=None,
                    )
                    self._log(
                        "自动运行完成："
                        f"抓取到={result['crawled']}，"
                        f"新增入库={result['inserted']}，"
                        f"已推送={result['notified']}"
                    )
                except Exception as exc:
                    self._log(f"自动运行失败：{exc}")
                self.stop_event.wait(interval_minutes * 60)

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def stop_auto_run(self) -> None:
        self.stop_event.set()
        self._log("已请求停止自动运行")

    def export_csv(self) -> None:
        if not self.last_items:
            messagebox.showinfo("提示", "请先点击“获取今日招标信息”。")
            return

        path = filedialog.asksaveasfilename(
            title="保存 CSV",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"tender_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not path:
            return

        fields = ["title", "source", "published_at", "matched_keywords", "url"]
        with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in self.last_items:
                writer.writerow(
                    {
                        "title": item.get("title", ""),
                        "source": item.get("source", ""),
                        "published_at": item.get("published_at", ""),
                        "matched_keywords": "、".join(
                            str(keyword)
                            for keyword in item.get("matched_keywords", [])
                        ),
                        "url": item.get("url", ""),
                    }
                )
        self._log(f"CSV 已保存：{path}")


def main() -> None:
    app = TenderMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

