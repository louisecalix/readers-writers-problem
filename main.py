import threading
import json
import os
import tkinter as tk
from tkinter import ttk
from threading import Thread, Event, Semaphore
import time

def load_nfts():
    if os.path.exists("nfts.json"):
        with open("nfts.json", "r") as file:
            return json.load(file)
    return [{"name": "NFT 1"}, {"name": "NFT 2"}, {"name": "NFT 3"}, {"name": "NFT 4"}, {"name": "NFT 5"}]

def save_nfts(nfts):
    with open("nfts.json", "w") as file:
        json.dump(nfts, file, indent=4)

nfts = load_nfts()
updating_nfts = {}
reader_stop_event = Event()
writer_done_event = Event()
terminate_event = Event()

writer_semaphore = Semaphore(1)
reader_semaphore = Semaphore(5)
buy_semaphore = Semaphore(1)

buyer_count = 0
seller_count = 0
buyer_windows = []
current_nft_index = 0

def update_nft_list(listbox, exclude=None):
    if not listbox.winfo_exists():
        return
    selected_indices = listbox.curselection()
    selected_items = [listbox.get(i) for i in selected_indices] if selected_indices else []
    listbox.delete(0, tk.END)
    for nft in nfts:
        if nft["name"] != exclude and nft["name"] not in updating_nfts:
            listbox.insert(tk.END, nft["name"])
    for i, item in enumerate(listbox.get(0, tk.END)):
        if item in selected_items:
            listbox.select_set(i)

def create_buyer_window(parent):
    global buyer_count, buyer_windows
    buyer_count += 1
    buyer_window = tk.Toplevel(parent)
    buyer_window.title(f"Buyer Window {buyer_count}")
    buyer_windows.append(buyer_window)

    nft_listbox = tk.Listbox(buyer_window, width=40, height=10)
    nft_listbox.pack(pady=10)

    status_label = tk.Label(buyer_window, text="Not viewing any products")
    status_label.pack(pady=5)

    log_text = tk.Text(buyer_window, height=10, width=50, state="disabled", wrap="word")
    log_text.pack(pady=10)

    current_nft_label = tk.Label(buyer_window, text="Currently viewing: None")
    current_nft_label.pack(pady=5)

    def log(message):
        if log_text.winfo_exists():
            log_text.config(state="normal")
            log_text.insert(tk.END, f"{message}\n")
            log_text.config(state="disabled")
            log_text.see(tk.END)

    def buy_nft(nft_name):
        def perform_buy():
            buy_semaphore.acquire()
            try:
                for nft in nfts:
                    if nft["name"] == nft_name:
                        nfts.remove(nft)
                        save_nfts(nfts)
                        log(f"Successfully bought {nft_name}.")
                        update_nft_list(nft_listbox)
                        update_reader_views()
                        return
                log(f"{nft_name} is no longer available.")
            finally:
                buy_semaphore.release()

        Thread(target=perform_buy).start()

    buy_button = tk.Button(buyer_window, text="Buy NFT", command=lambda: buy_nft(current_nft_label.cget("text").split(": ")[-1]))
    buy_button.pack(pady=5)

    def start_reader():
        start_button.config(state=tk.DISABLED)
        global current_nft_index

        def reader_task():
            try:
                reader_semaphore.acquire()
                nft_to_read = nfts[current_nft_index % len(nfts)]["name"]
                if current_nft_label.winfo_exists():
                    current_nft_label.config(text=f"Currently viewing: {nft_to_read}")
                if status_label.winfo_exists():
                    status_label.config(text="Reading")
                log(f"Buyer is viewing {nft_to_read}.")
                time.sleep(5)
                if reader_stop_event.is_set() and updating_nfts.get(nft_to_read):
                    log(f"Buyer has been interrupted by a seller.")
                else:
                    log(f"Buyer finished viewing {nft_to_read}.")
            finally:
                if status_label.winfo_exists():
                    status_label.config(text="Not viewing")
                if current_nft_label.winfo_exists():
                    current_nft_label.config(text="Currently viewing: None")
                if start_button.winfo_exists():
                    start_button.config(state=tk.NORMAL)
                reader_semaphore.release()

        update_nft_list(nft_listbox)
        Thread(target=reader_task).start()

    start_button = tk.Button(buyer_window, text="Start Viewing", command=start_reader)
    start_button.pack(pady=5)

    def refresh_reader_view():
        if not terminate_event.is_set() and nft_listbox.winfo_exists():
            update_nft_list(nft_listbox)
            buyer_window.after(1000, refresh_reader_view)

    refresh_reader_view()

    def auto_view_nfts():
        while not terminate_event.is_set():
            if buyer_window.winfo_exists():
                start_reader()
                time.sleep(10)

    Thread(target=auto_view_nfts).start()

    def on_close():
        terminate_event.set()
        buyer_windows.remove(buyer_window)
        buyer_window.destroy()

    buyer_window.protocol("WM_DELETE_WINDOW", on_close)

def create_seller_window(parent):
    global seller_count
    seller_count += 1
    seller_window = tk.Toplevel(parent)
    seller_window.title(f"Seller Window {seller_count}")

    nft_listbox = tk.Listbox(seller_window, width=40, height=10)
    nft_listbox.pack(pady=10)

    log_text = tk.Text(seller_window, height=10, width=50, state="disabled", wrap="word")
    log_text.pack(pady=10)

    selected_nft_label = tk.Label(seller_window, text="Selected NFT: None")
    selected_nft_label.pack(pady=5)

    input_field = tk.Entry(seller_window, width=40)
    input_field.pack(pady=5)
    input_field.pack_forget()

    save_button = tk.Button(seller_window, text="Save Update", command=lambda: done_writing(log))
    save_button.pack(pady=5)
    save_button.pack_forget()

    def log(message):
        if log_text.winfo_exists():
            log_text.config(state="normal")
            log_text.insert(tk.END, f"{message}\n")
            log_text.config(state="disabled")
            log_text.see(tk.END)

    def select_nft_to_update():
        selected_indices = nft_listbox.curselection()
        if not selected_indices:
            log("No NFT selected for updating.")
            return

        selected_nft = nft_listbox.get(selected_indices[0])

        if selected_nft in updating_nfts:
            log("Another seller is currently updating this NFT. Try updating a different NFT.")
            return

        log(f"Seller selected {selected_nft} for updating.")
        selected_nft_label.config(text=f"Selected NFT: {selected_nft}")
        nft_listbox.delete(selected_indices[0])

        input_field.delete(0, tk.END)
        input_field.insert(0, selected_nft)
        input_field.pack(pady=5)
        save_button.pack(pady=5)
        start_writer_task(selected_nft, log, nft_listbox, input_field)

        update_reader_views() # ud buyer window to see removed NFT

    def start_writer_task(selected_nft, log, nft_listbox, input_field):
        Thread(target=writer_task, args=(selected_nft, log, nft_listbox, input_field)).start()

    select_button = tk.Button(seller_window, text="Select NFT to Update", command=select_nft_to_update)
    select_button.pack(pady=5)

    update_nft_list(nft_listbox, exclude=None)

    def auto_update_nfts():
        while not terminate_event.is_set():
            select_nft_to_update()
            time.sleep(3)

    Thread(target=auto_update_nfts).start()

    def on_close():
        terminate_event.set()
        seller_window.destroy()

    seller_window.protocol("WM_DELETE_WINDOW", on_close)

def done_writing(log):
    writer_done_event.set()
    log("Seller saved the update.")
    save_nfts(nfts)
    update_reader_views() # ud buyer window to reflect the updated NFT


def writer_task(selected_nft, log, nft_listbox, input_field):
    global updating_nfts, nfts
    writer_semaphore.acquire()
    try:
        updating_nfts[selected_nft] = True
        reader_stop_event.set()
        log(f"Seller started updating {selected_nft}.")
        time.sleep(1)

        for nft in nfts:
            if nft["name"] == selected_nft:
                nfts.remove(nft)
                break

        writer_done_event.wait()
        writer_done_event.clear()

        updated_nft = {"name": input_field.get() or f"{selected_nft} (Updated)"}
        nfts.append(updated_nft)
        save_nfts(nfts)

        log(f"Seller finished updating {selected_nft} to {updated_nft['name']}.")

        del updating_nfts[selected_nft]
        reader_stop_event.clear()
        update_reader_views()
        update_nft_list(nft_listbox)
    finally:
        writer_semaphore.release()

def update_reader_views():
    for widget in tk._default_root.winfo_children():
        if isinstance(widget, tk.Toplevel) and "Buyer Window" in widget.title():
            for child in widget.winfo_children():
                if isinstance(child, tk.Listbox):
                    update_nft_list(child, exclude=None)

def buy_all_nfts():
    for buyer_window in buyer_windows:
        for child in buyer_window.winfo_children():
            if isinstance(child, tk.Label) and "Currently viewing:" in child.cget("text"):
                nft_name = child.cget("text").split(": ")[-1]
                if nft_name != "None":
                    for widget in buyer_window.winfo_children():
                        if isinstance(widget, tk.Button) and widget.cget("text") == "Buy NFT":
                            widget.invoke()


def main():
    root = tk.Tk()
    root.title("NFT Manager")
    root.geometry("350x300")
    root.configure(bg="lightblue")

    style = ttk.Style()
    style.configure("TButton",
                    font=("Helvetica", 16),
                    padding=10,
                    foreground="black",
                    background="blue")

    title_frame = tk.Frame(root, bg="lightblue")
    title_frame.pack(fill=tk.X, pady=20)

    style = ttk.Style()
    style.configure("Title.TLabel", background="lightblue", font=("Helvetica", 20))

    title_label = ttk.Label(title_frame, text="NFT Manager Simulation", style="Title.TLabel")
    title_label.pack(pady=20)

    def startsimulation():

        for _ in range(2):
            create_buyer_window(root)
            create_seller_window(root)

        # create_buyer_window(root)
        # create_seller_window(root)

    start_simulation = ttk.Button(root, text="Start Simulation", command=startsimulation)
    start_simulation.pack(pady=10)

    # def summon_second_seller_window():
    #     create_seller_window(root)

    # second_seller_button = ttk.Button(root, text="Add Seller", command=summon_second_seller_window)
    # second_seller_button.pack(pady=10)

    # def summon_second_buyer_window():
    #     create_buyer_window(root)

    # second_buyer_button = ttk.Button(root, text="Add Buyer", command=summon_second_buyer_window)
    # second_buyer_button.pack(pady=10)

    def simulate_buy():
        buy_all_nfts()

    simulate_buy_button = ttk.Button(root, text="Simulate Buy", command=simulate_buy)
    simulate_buy_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
