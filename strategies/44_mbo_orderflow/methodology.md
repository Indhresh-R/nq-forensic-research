# Strategy 44: Forensic Microstructure Methodology

## 1. Data Ingestion & Causal Architecture

All order flow research consumes binary Databento `.dbn.zst` files from `d:\NQ-2\data\mbo_full_state_50\`.

```text
[DBN Record Stream]
        │
        ├── Record Flags Check (F_SNAPSHOT, F_LAST)
        │       └── Initial Snapshot -> LimitOrderBook.apply_record(is_snapshot=True)
        │
        └── Continuous Stream (00:00 to 16:00 UTC)
                └── Real-time mutations -> LimitOrderBook.apply_record(is_snapshot=False)
```

### Critical Invariants
1. **Zero Re-Engineering of Engine:** [`d:\NQ-2\common\order_book.py`](file:///d:/NQ-2/common/order_book.py) is read-only.
2. **Deterministic Message Sequencing:** CME Globex MDP 3.0 sends atomic sequence-numbered packets. Iterating sequentially through `db.DBNStore.from_file()` guarantees FIFO queue priority preservation.
3. **No Inter-Record Interpolation:** Order book state at clock time $T$ is defined as the exact state resulting from the last event where $\text{ts\_event} \le T$.

---

## 2. Sampling Grid & Time Windows

For each session date $D$:
* **Session Window:** `09:30:00 EDT` to `12:00:00 EDT` (`13:30:00 UTC` to `16:00:00 UTC`).
* **Sampling Frequency:** $\Delta t = 1.0\text{ second}$ (9,000 observations per session).
* **Warm-up Period:** Midnight UTC (`00:00:00`) to Cash Open (`13:30:00 UTC`) is fully replayed to ensure the 09:30 EDT book state has 100% resting depth accuracy.

---

## 3. Mathematical Feature Formulations

### H01: Depth Imbalance
Let $P_b^i(t)$ and $Q_b^i(t)$ be the price and total resting quantity at bid level $i$ (where $i=1$ is Best Bid).
Let $P_a^i(t)$ and $Q_a^i(t)$ be the price and total resting quantity at ask level $i$ (where $i=1$ is Best Ask).

* **Top-of-Book Imbalance ($OBI_1$):**
  $$OBI_1(t) = \frac{Q_b^1(t) - Q_a^1(t)}{Q_b^1(t) + Q_a^1(t)} \in [-1.0, 1.0]$$

* **Top-5 Level Imbalance ($OBI_5$):**
  $$OBI_5(t) = \frac{\sum_{i=1}^5 Q_b^i(t) - \sum_{i=1}^5 Q_a^i(t)}{\sum_{i=1}^5 Q_b^i(t) + \sum_{i=1}^5 Q_a^i(t)} \in [-1.0, 1.0]$$

* **Weighted Depth Imbalance ($WOBI_5$):**
  $$WOBI_5(t) = \frac{\sum_{i=1}^5 \frac{Q_b^i(t)}{i} - \sum_{i=1}^5 \frac{Q_a^i(t)}{i}}{\sum_{i=1}^5 \frac{Q_b^i(t)}{i} + \sum_{i=1}^5 \frac{Q_a^i(t)}{i}}$$

---

### H02: Aggressive Order Flow Delta
During continuous streaming, aggressive trade executions (`action == 'T'`) are accumulated into rolling time windows $w \in \{1s, 5s, 15s, 60s\}$:

* Buy volume $V_{\text{buy}, w}(t) = \sum \text{size}$ for trades with $\text{side} == 'B'$ (buyer crossed spread).
* Sell volume $V_{\text{sell}, w}(t) = \sum \text{size}$ for trades with $\text{side} == 'A'$ (seller crossed spread).
* **Cumulative Volume Delta ($CVD_w$):**
  $$\Delta V_w(t) = V_{\text{buy}, w}(t) - V_{\text{sell}, w}(t)$$
* **Normalized Flow Ratio ($NFR_w$):**
  $$NFR_w(t) = \frac{V_{\text{buy}, w}(t) - V_{\text{sell}, w}(t)}{V_{\text{buy}, w}(t) + V_{\text{sell}, w}(t) + \epsilon}$$

---

### H03: Passive Absorption
Absorption occurs when market participants absorb aggressive order flow at the inside market without permitting price displacement.

* Let $\Delta P_w(t) = P_{\text{mid}}(t) - P_{\text{mid}}(t - w)$.
* If aggressive buyers dominate ($\Delta V_w(t) \ge \theta_{\text{high}}$) but price fails to rise ($\Delta P_w(t) \le 0$), liquidity absorption has occurred on the ask side.
* **Absorption Metric:**
  $$Absorb_{\text{bearish}}(t) = \mathbb{I}(\Delta P_w(t) \le 0) \cdot \max(0, \Delta V_w(t))$$
  $$Absorb_{\text{bullish}}(t) = \mathbb{I}(\Delta P_w(t) \ge 0) \cdot \max(0, -\Delta V_w(t))$$

---

### H04: Queue Cancellation Dynamics
Using order cancellation events (`action == 'C'`):
* Total cancelled bid volume $C_b,w(t)$ and ask volume $C_a,w(t)$ over window $w$.
* **Cancellation Skew ($CS_w$):**
  $$CS_w(t) = \frac{C_b,w(t) - C_a,w(t)}{C_b,w(t) + C_a,w(t) + \epsilon}$$

---

## 4. Evaluation Metrics & Statistical Testing

1. **Spearman Rank Information Coefficient ($IC$):**
   $$IC_\tau = \text{corr}_{\text{rank}}(F(t), \Delta P_{t + \tau})$$
   Evaluated independently per session and pooled across In-Sample sessions.

2. **t-Statistic on Mean IC:**
   $$\text{IR} = \frac{\text{Mean}(IC_{\text{session}})}{\text{Std}(IC_{\text{session}})}, \quad t = \text{IR} \cdot \sqrt{N_{\text{sessions}}}$$

3. **Quintile Sorting:**
   Rank observations into $Q_1, Q_2, Q_3, Q_4, Q_5$. Compute:
   $$\bar{r}_k(\tau) = \frac{1}{|Q_k|} \sum_{t \in Q_k} \Delta P_{t, \tau}$$
   Verify monotonic ordering across quintiles.
