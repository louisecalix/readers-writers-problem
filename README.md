# NFT Manager Simulation

This project is a **Tkinter-based simulation** of an NFT management system. It allows multiple buyers and sellers to interact with a shared pool of NFTs using **multithreading**, providing realistic concurrency scenarios such as buying, selling, and updating NFTs.

---

## Key Highlight: Solving the Readers-Writers Problem

The simulation **effectively addresses the classic Readers-Writers problem** using semaphores and threading. The following strategies are implemented:

1. **Readers-Writers Balance**:
   - Buyers (readers) can view NFTs concurrently, as long as no seller is updating them.
   - Sellers (writers) are given priority when updating an NFT, ensuring that data remains consistent and accurate.

2. **Concurrency Control**:
   - A **semaphore** is used to regulate access, preventing race conditions.
   - Sellers (writers) temporarily block buyers (readers) from interacting with the NFT being updated.

3. **Thread-Safe Design**:
   - Multiple threads (buyers and sellers) operate in parallel without compromising the integrity of the shared NFT pool.

---

## Features

- **Buyer Window**:
  - View available NFTs.
  - Buy NFTs, which removes them from the shared pool.
  - Log activity while viewing or buying NFTs.
  
- **Seller Window**:
  - Update existing NFTs.
  - Add new NFTs to the shared pool.
  - Log activity while updating NFTs.

- **Concurrency**:
  - Multiple buyers and sellers can operate simultaneously.
  - Uses semaphores to ensure safe interaction with shared resources.

---

## How It Works

1. **Buyers**:
   - Buyers can view NFTs and purchase them.
   - Viewing is limited to a specific number of concurrent buyers.

2. **Sellers**:
   - Sellers can select an NFT to update.
   - Sellers temporarily block buyers from interacting with the NFT they are updating.

3. **Thread Synchronization**:
   - **Semaphore** ensures controlled access to shared resources.
   - **Event** objects signal and coordinate actions between threads.

---

## Files

- **nft_data.json**: Stores the current list of NFTs.
- **main.py**: The primary script for running the application.

---

### Requirements

- Python 3.7+
- Libraries:
  - `tkinter` (standard library)
  - `threading` (standard library)
  - `json` (standard library)


