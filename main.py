import tkinter as tk
from tkinter import ttk
from threading import Thread, Event, Semaphore
import threading
import time
import json
import os

def load_nfts():
    if os.path.exists("nfts.json"):
        with open("nfts.json", "r") as file:
            return json.load(file)
    return [{"name": "NFT 1"},
            {"name": "NFT 2"},
            {"name": "NFT 3"},
            {"name": "NFT 4"},
            {"name": "NFT 5"}]


def save_nfts(nfts):
    with open("nfts.json", "w") as file:
        json.dump(nfts, file, indent=4)



nfts = load_nfts()
updating_nft = None
reader_stop_event = Event()
writer_done_event = Event()
terminate_event = Event()

writer_semaphore = Semaphore(1)  
reader_semaphore = Semaphore(5)  
buy_semaphore = Semaphore(1)

buyer_count = 0
seller_count = 0


# def update_nft_list(listbox, exclude=None):
#     listbox.delete(0, tk.END)
#     for nft in nfts:
#         if nft["name"] != exclude:
#             listbox.insert(tk.END, nft["name"])


def update_nft_list(listbox, exclude=None):
    # Save current selection
    selected_indices = listbox.curselection()
    selected_items = [listbox.get(i) for i in selected_indices] if selected_indices else []

    # Clear and update the listbox
    listbox.delete(0, tk.END)
    for nft in nfts:
        if nft["name"] != exclude:
            listbox.insert(tk.END, nft["name"])

    # Restore the selection if it exists
    for i, item in enumerate(listbox.get(0, tk.END)):
        if item in selected_items:
            listbox.select_set(i)

            

def create_buyer_window(parent):
    global buyer_count
    buyer_count += 1
    buyer_window = tk.Toplevel(parent)
    buyer_window.title(f"Buyer Window {buyer_count}")

    nft_listbox = tk.Listbox(buyer_window, width=40, height=10)
    nft_listbox.pack(pady=10)

    status_label = tk.Label(buyer_window, text="Not viewing any products")
    status_label.pack(pady=5)

    log_text = tk.Text(buyer_window, height=10, width=50, state="disabled", wrap="word")
    log_text.pack(pady=10)

    current_nft_label = tk.Label(buyer_window, text="Currently viewing: None")
    current_nft_label.pack(pady=5)

    def log(message):
        log_text.config(state="normal")
        log_text.insert(tk.END, f"{message}\n")
        log_text.config(state="disabled")
        log_text.see(tk.END)

    def buy_nft():
        selected_indices = nft_listbox.curselection()
        if not selected_indices:
            log("No NFT selected for buying.")
            return

        selected_nft = nft_listbox.get(selected_indices[0])

        def perform_buy():
            buy_semaphore.acquire()
            try:
                for nft in nfts:
                    if nft["name"] == selected_nft:
                        nfts.remove(nft)
                        save_nfts(nfts)
                        log(f"Successfully bought {selected_nft}.")
                        update_nft_list(nft_listbox)
                        return
                log(f"{selected_nft} is no longer available.")
            finally:
                buy_semaphore.release()

        Thread(target=perform_buy).start()

    buy_button = tk.Button(buyer_window, text="Buy NFT", command=buy_nft)
    buy_button.pack(pady=5)

    def start_reader():
        start_button.config(state=tk.DISABLED)

        def reader_task():
            try:
                reader_semaphore.acquire()
                nft_to_read = nfts[threading.get_ident() % len(nfts)]["name"]
                if current_nft_label.winfo_exists():
                    current_nft_label.config(text=f"Currently viewing: {nft_to_read}")
                if status_label.winfo_exists():
                    status_label.config(text="Reading")

                log(f"Buyer is viewing {nft_to_read}.")
                time.sleep(6)
                # log(f"Buyer finished viewing {nft_to_read}.")

                if reader_stop_event.is_set() and updating_nft == nft_to_read:
                    log(f"Buyer has been interrupted by a seller.")
                else:
                    log(f"Buyer finished viewing {nft_to_read}.")


            finally:
                if status_label.winfo_exists():
                    status_label.config(text="Not viewing")
                if current_nft_label.winfo_exists():
                    current_nft_label.config(text="Currently viewing: None")
                start_button.config(state=tk.NORMAL)
                reader_semaphore.release()

        update_nft_list(nft_listbox)
        Thread(target=reader_task).start()

    start_button = tk.Button(buyer_window, text="Start Viewing", command=start_reader)
    start_button.pack(pady=5)

    def refresh_reader_view():
        if not terminate_event.is_set():
            update_nft_list(nft_listbox)
            buyer_window.after(1000, refresh_reader_view)

    refresh_reader_view()



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
        log_text.config(state="normal")
        log_text.insert(tk.END, f"{message}\n")
        log_text.config(state="disabled")
        log_text.see(tk.END)

    def select_nft_to_update():
        selected_indices = nft_listbox.curselection()
        if not selected_indices:
            log("No NFT selected for updating.")
            return

        if updating_nft is not None:
            log("Another seller is currently updating this NFT. Try again later.")
            return

        selected_nft = nft_listbox.get(selected_indices[0])
        selected_nft_label.config(text=f"Selected NFT: {selected_nft}")
        nft_listbox.delete(selected_indices[0])

        input_field.delete(0, tk.END)
        input_field.insert(0, selected_nft)
        input_field.pack(pady=5)
        save_button.pack(pady=5)
        start_writer_task(selected_nft, log, nft_listbox, input_field)

    def start_writer_task(selected_nft, log, nft_listbox, input_field):
        Thread(target=writer_task, args=(selected_nft, log, nft_listbox, input_field)).start()

    select_button = tk.Button(
        seller_window, text="Select NFT to Update", command=select_nft_to_update
    )
    select_button.pack(pady=5)

    update_nft_list(nft_listbox, exclude=updating_nft)



def done_writing(log):
    writer_done_event.set()
    log("Seller saved the update.")
    save_nfts(nfts)



def writer_task(selected_nft, log, nft_listbox, input_field):
    global updating_nft, nfts

    writer_semaphore.acquire()
    try:
        # if updating_nft is not None and updating_nft != selected_nft:
        #     log(f"Seller cannot update {selected_nft} because {updating_nft} is currently being updated.")
        #     return
        # elif updating_nft == selected_nft:
        #     log(f"Seller is already updating {selected_nft}.")
        #     return


        updating_nft = selected_nft
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


        updating_nft = None
        reader_stop_event.clear()  
        update_reader_views()
        update_nft_list(nft_listbox)
    finally:
        writer_semaphore.release()



def update_reader_views():
    for widget in tk._default_root.winfo_children():
        if isinstance(widget, tk.Toplevel) and "Reader Window" in widget.title():
            for child in widget.winfo_children():
                if isinstance(child, tk.Listbox):
                    update_nft_list(child, exclude=updating_nft)



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


    # title_label = ttk.Label(root, text="NFT Manager", bg="lightblue", font=("Helvetica", 20))
    # title_label.pack(pady=20)

    def startsimulation():
        create_buyer_window(root)
        create_seller_window(root)

    start_simulation = ttk.Button(root, text="Start Simulation", command=startsimulation)
    start_simulation.pack(pady=10)


    # buyer_button = ttk.Button(root, text="Open Buyer Window", command=lambda: create_buyer_window(root))
    # buyer_button.pack(pady=10)

    # seller_button = ttk.Button(root, text="Open Seller Window", command=lambda: create_seller_window(root))
    # seller_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()