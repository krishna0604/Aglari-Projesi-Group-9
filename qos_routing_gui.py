import tkinter as tk
from tkinter import ttk, messagebox
import random
import math

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ======================================================
# 1) Ağ Oluşturma ve Metrik Hesaplama Fonksiyonları
# ======================================================

def generate_random_network(n_nodes=250, p=0.4):
    G = nx.erdos_renyi_graph(n_nodes, p)

    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    for node in G.nodes():
        processing_delay = random.uniform(0.5, 2.0)  # ms
        node_reliability = random.uniform(0.95, 0.999)
        G.nodes[node]["processing_delay"] = processing_delay
        G.nodes[node]["node_reliability"] = node_reliability

    for u, v in G.edges():
        bandwidth = random.uniform(100, 1000)      # Mbps
        link_delay = random.uniform(3, 15)         # ms
        link_reliability = random.uniform(0.95, 0.999)

        G.edges[u, v]["bandwidth"] = bandwidth
        G.edges[u, v]["link_delay"] = link_delay
        G.edges[u, v]["link_reliability"] = link_reliability

    return G


def compute_total_delay(G, path):
    if len(path) < 2:
        return 0.0

    link_delay_sum = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link_delay_sum += G.edges[u, v]["link_delay"]

    processing_sum = 0.0
    for node in path[1:-1]:
        processing_sum += G.nodes[node]["processing_delay"]

    return link_delay_sum + processing_sum


def compute_reliability_cost(G, path):
    if len(path) == 0:
        return float("inf")

    rel_cost = 0.0

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link_rel = G.edges[u, v]["link_reliability"]
        rel_cost += -math.log(link_rel)

    for node in path:
        node_rel = G.nodes[node]["node_reliability"]
        rel_cost += -math.log(node_rel)

    return rel_cost


def compute_resource_cost(G, path, max_bw=1000.0):
    if len(path) < 2:
        return float("inf")

    res_cost = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        bw = G.edges[u, v]["bandwidth"]
        res_cost += max_bw / bw

    return res_cost


def compute_total_cost(delay, rel_cost, res_cost, w_delay, w_rel, w_res):
    return w_delay * delay + w_rel * rel_cost + w_res * res_cost


def find_best_path_simple(G, source, target, w_delay, w_rel, w_res):
    """Basit: çok amaçlı maliyeti kenar ağırlığına çevirip Dijkstra ile yol bulma."""
    if source == target:
        return [source]

    def edge_weight(u, v, data):
        link_delay = data["link_delay"]
        proc_delay = G.nodes[v]["processing_delay"]

        node_rel_u = G.nodes[u]["node_reliability"]
        node_rel_v = G.nodes[v]["node_reliability"]
        link_rel = data["link_reliability"]
        edge_rel_cost = -math.log(link_rel) - math.log(node_rel_u) - math.log(node_rel_v)

        bandwidth = data["bandwidth"]
        res_cost = 1000.0 / bandwidth

        total_delay_edge = link_delay + proc_delay

        return compute_total_cost(
            total_delay_edge,
            edge_rel_cost,
            res_cost,
            w_delay,
            w_rel,
            w_res,
        )

    try:
        path = nx.dijkstra_path(
            G,
            source=source,
            target=target,
            weight=lambda u, v, d: edge_weight(u, v, d),
        )
        return path
    except nx.NetworkXNoPath:
        return None


# ======================================================
# 3) GUI Uygulaması
# ======================================================

class QoSRoutingApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("QoS Çok Amaçlı Yönlendirme - GUI Demo")
        self.geometry("1300x720")
        self.configure(bg="#f5f5f7")

        self.dark_mode = False
        self.selected_node = None
        self.last_path = None
        self.hover_node = None
        self.hover_annot = None
        self.norm_popup = None

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.light_bg_main = "#f5f5f7"
        self.light_bg_side = "#f2f2f6"
        self.light_card = "#ffffff"
        self.light_node_color = "#4a90e2"
        self.light_edge_color = "#bbbbbb"

        self.dark_bg_main = "#202124"
        self.dark_bg_side = "#2b2c2f"
        self.dark_card = "#30343a"
        self.dark_node_color = "#8ab4f8"
        self.dark_edge_color = "#5f6368"

        self.style = style
        self._init_styles()

        self.G = None
        self.pos = None

        self._build_layout()

    # ---------------- Styles ----------------

    def _init_styles(self):
        s = self.style

        s.configure("Main.TFrame", background=self.light_bg_main)
        s.configure("Side.TFrame", background=self.light_bg_side)

        s.configure(
            "Card.TLabelframe",
            background=self.light_card,
            relief="flat",
            borderwidth=0,
        )
        s.configure(
            "Card.TLabelframe.Label",
            font=("Segoe UI", 11, "bold"),
            background=self.light_card,
        )

        s.configure("TLabel", background=self.light_card, font=("Segoe UI", 9))
        s.configure("Small.TLabel", background=self.light_card, font=("Segoe UI", 8))

        s.configure(
            "Accent.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#4a90e2",
            foreground="white",
            borderwidth=0,
            padding=(10, 5),
        )
        s.map(
            "Accent.TButton",
            background=[("active", "#3b7ac0")],
            foreground=[("disabled", "#cccccc")],
        )

        s.configure(
            "Ghost.TButton",
            font=("Segoe UI", 8),
            background="#e0e0e5",
            foreground="#333333",
            borderwidth=0,
            padding=(6, 3),
        )
        s.map(
            "Ghost.TButton",
            background=[("active", "#d0d0dd")],
        )

        s.configure(
            "Modern.Horizontal.TScale",
            troughcolor="#d0d0dd",
            background=self.light_card,
            borderwidth=0,
            sliderlength=18,
        )

    def _apply_theme(self):
        if self.dark_mode:
            bg_main = self.dark_bg_main
            bg_side = self.dark_bg_side
            card = self.dark_card
            fg_text = "#e8eaed"
            node_color = self.dark_node_color
            edge_color = self.dark_edge_color
            edge_alpha = 0.12
        else:
            bg_main = self.light_bg_main
            bg_side = self.light_bg_side
            card = self.light_card
            fg_text = "#000000"
            node_color = self.light_node_color
            edge_color = self.light_edge_color
            edge_alpha = 0.15

        self.configure(bg=bg_main)
        self.style.configure("Main.TFrame", background=bg_main)
        self.style.configure("Side.TFrame", background=bg_side)
        self.style.configure("Card.TLabelframe", background=card)
        self.style.configure("Card.TLabelframe.Label", background=card, foreground=fg_text)
        self.style.configure("TLabel", background=card, foreground=fg_text)
        self.style.configure("Small.TLabel", background=card, foreground=fg_text)

        self.style.configure(
            "Modern.Horizontal.TScale",
            background=card,
            troughcolor="#3a3f47" if self.dark_mode else "#d0d0dd",
        )

        if self.dark_mode:
            self.results_text.config(bg="#202124", fg="#e8eaed", insertbackground="#e8eaed")
            self.fig.patch.set_facecolor(self.dark_bg_main)
            self.ax.set_facecolor(self.dark_bg_main)
        else:
            self.results_text.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
            self.fig.patch.set_facecolor("#ffffff")
            self.ax.set_facecolor("#ffffff")

        self.current_node_color = node_color
        self.current_edge_color = edge_color
        self.current_edge_alpha = edge_alpha

        self._draw_graph(path=self.last_path)

        if self.norm_popup is not None:
            self._style_norm_popup()

    # ---------------- GUI Yapısı ----------------

    def _build_layout(self):
        main_frame = ttk.Frame(self, padding=5, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, style="Main.TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(main_frame, width=320, style="Side.TFrame")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        # Matplotlib Figure
        self.fig = Figure(figsize=(6.5, 5.8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Ağ Topolojisi (N ≈ 250)")
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("motion_notify_event", self.on_canvas_hover)
        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)

        self.hover_annot = None

        # Top bar: Dark mode
        top_bar = ttk.Frame(right_frame, style="Side.TFrame")
        top_bar.pack(fill=tk.X, pady=(0, 4))

        self.dark_btn = ttk.Button(
            top_bar,
            text="Karanlık Mod: Kapalı",
            style="Ghost.TButton",
            command=self.toggle_dark_mode,
        )
        self.dark_btn.pack(side=tk.RIGHT, padx=4, pady=4)

        # ---- Ağ Kontrolleri (Card) ----
        network_frame = ttk.LabelFrame(
            right_frame,
            text="Ağ Kontrolleri",
            style="Card.TLabelframe",
            padding=10,
        )
        network_frame.pack(fill=tk.X, pady=(0, 8))

        self.btn_generate = ttk.Button(
            network_frame,
            text="Ağı Oluştur",
            style="Accent.TButton",
            command=self.on_generate_network,
        )
        self.btn_generate.pack(fill=tk.X, pady=3)

        sd_frame = ttk.Frame(network_frame, style="Card.TLabelframe")
        sd_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sd_frame, text="Kaynak (S):").grid(row=0, column=0, sticky="w")
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(
            sd_frame, textvariable=self.source_var, state="readonly"
        )
        self.source_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        ttk.Label(sd_frame, text="Hedef (D):").grid(row=1, column=0, sticky="w")
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(
            sd_frame, textvariable=self.dest_var, state="readonly"
        )
        self.dest_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        sd_frame.columnconfigure(1, weight=1)

        # ---- Algoritma Seçimi (Card) ----
        algo_frame = ttk.LabelFrame(
            right_frame,
            text="Algoritma Seçimi",
            style="Card.TLabelframe",
            padding=10,
        )
        algo_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(algo_frame, text="Algoritma:").pack(anchor="w")

        self.algorithms = [
            "Basit (Dijkstra-türevi)",
            "Genetik Algoritma (Grup 1)",
            "Karınca Kolonisi (Grup 1)",
            "Q-Learning (Grup 2)",
        ]
        self.alg_var = tk.StringVar(value=self.algorithms[0])

        self.alg_combo = ttk.Combobox(
            algo_frame,
            textvariable=self.alg_var,
            values=self.algorithms,
            state="readonly",
        )
        self.alg_combo.pack(fill=tk.X, pady=4)

        ttk.Label(
            algo_frame,
            text="Not: Şu anda yalnızca 'Basit' algoritma çalışıyor.\n"
                 "Diğerleri Grup 1 ve Grup 2 tarafından eklenecek.",
            style="Small.TLabel",
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # ---- Ağırlıklar (Card) ----
        weights_frame = ttk.LabelFrame(
            right_frame,
            text="Ağırlıklar (Wdelay, Wrel, Wres)",
            style="Card.TLabelframe",
            padding=10,
        )
        weights_frame.pack(fill=tk.X, pady=(0, 8))

        self.w_delay = tk.DoubleVar(value=5.0)
        self.w_rel = tk.DoubleVar(value=3.0)
        self.w_res = tk.DoubleVar(value=2.0)

        ttk.Label(weights_frame, text="Gecikme Ağırlığı (Wdelay)").pack(anchor="w")
        self.slider_delay = ttk.Scale(
            weights_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.w_delay,
            style="Modern.Horizontal.TScale",
        )
        self.slider_delay.pack(fill=tk.X, pady=2)

        ttk.Label(weights_frame, text="Güvenilirlik Ağırlığı (Wrel)").pack(anchor="w")
        self.slider_rel = ttk.Scale(
            weights_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.w_rel,
            style="Modern.Horizontal.TScale",
        )
        self.slider_rel.pack(fill=tk.X, pady=2)

        ttk.Label(weights_frame, text="Kaynak Ağırlığı (Wres)").pack(anchor="w")
        self.slider_res = ttk.Scale(
            weights_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.w_res,
            style="Modern.Horizontal.TScale",
        )
        self.slider_res.pack(fill=tk.X, pady=2)

        # Normalize label + popup
        self.weights_sum_label = ttk.Label(
            weights_frame,
            text="",
            style="Small.TLabel",
            wraplength=260,
            justify="left",
        )
        self.weights_sum_label.pack(anchor="w", pady=(6, 2))

        self.weights_sum_label.bind("<ButtonPress-1>", self.on_norm_press)
        self.weights_sum_label.bind("<B1-Motion>", self.on_norm_drag)
        self.weights_sum_label.bind("<ButtonRelease-1>", self.on_norm_release)

        self._update_weights_label()

        self.slider_delay.bind(
            "<ButtonRelease-1>", lambda e: self._update_weights_label()
        )
        self.slider_rel.bind(
            "<ButtonRelease-1>", lambda e: self._update_weights_label()
        )
        self.slider_res.bind(
            "<ButtonRelease-1>", lambda e: self._update_weights_label()
        )

        # ---- HESAPLA ----
        self.btn_compute = ttk.Button(
            right_frame,
            text="HESAPLA (En İyi Yolu Bul)",
            style="Accent.TButton",
            command=self.on_compute,
        )
        self.btn_compute.pack(fill=tk.X, pady=(0, 8))

        for btn in (self.btn_generate, self.btn_compute, self.dark_btn):
            btn.bind("<Enter>", lambda e, b=btn: b.state(["active"]))
            btn.bind("<Leave>", lambda e, b=btn: b.state(["!active"]))

        # ---- Sonuçlar (Card) ----
        results_frame = ttk.LabelFrame(
            right_frame, text="Sonuçlar", style="Card.TLabelframe", padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(
            results_frame,
            height=14,
            wrap="word",
            font=("Consolas", 9),
            bg="#ffffff",
            relief="flat",
            bd=1,
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.insert(
            tk.END, "Önce ağı oluşturun, sonra S/D ve ağırlıkları seçin.\n"
        )
        self.results_text.config(state=tk.DISABLED)

        self._apply_theme()

    # ---------------- Theme Toggle ----------------

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.dark_btn.config(text="Karanlık Mod: Açık")
        else:
            self.dark_btn.config(text="Karanlık Mod: Kapalı")
        self._apply_theme()

    # ---------------- Yardımcı Fonksiyonlar ----------------

    def _update_weights_label(self):
        d_raw = self.w_delay.get()
        r_raw = self.w_rel.get()
        s_raw = self.w_res.get()
        total = d_raw + r_raw + s_raw

        if total == 0:
            wd = wr = ws = 0.0
        else:
            wd = d_raw / total
            wr = r_raw / total
            ws = s_raw / total

        text = (
            "Normalize Edildi (toplam=1)\n"
            f"Wdelay={wd:.2f}, Wrel={wr:.2f}, Wres={ws:.2f}"
        )
        self.weights_sum_label.config(text=text)

        if self.norm_popup is not None:
            for child in self.norm_popup.winfo_children():
                if isinstance(child, tk.Frame):
                    for lbl in child.winfo_children():
                        if isinstance(lbl, tk.Label):
                            lbl.config(text=self._popup_text_from_norm(text))

    # -------- Normalize label popup --------

    def _popup_text_from_norm(self, label_text: str) -> str:
        parts = label_text.split("\n")
        if len(parts) >= 2:
            header = parts[0]
            vals = parts[1]
        else:
            header = "Normalize Edildi"
            vals = label_text
        vals_split = vals.split(",")
        vals_clean = "\n".join(v.strip() for v in vals_split)
        return header + "\n" + vals_clean

    def _style_norm_popup(self):
        if self.norm_popup is None:
            return
        bg = "#2b2c2f" if self.dark_mode else "#ffffff"
        fg = "#e8eaed" if self.dark_mode else "#000000"
        for child in self.norm_popup.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=bg)
                for lbl in child.winfo_children():
                    if isinstance(lbl, tk.Label):
                        lbl.config(bg=bg, fg=fg)

    def on_norm_press(self, event):
        text = self.weights_sum_label.cget("text")
        if not text:
            return

        if self.norm_popup is not None:
            self.norm_popup.destroy()

        self.norm_popup = tk.Toplevel(self)
        self.norm_popup.overrideredirect(True)
        self.norm_popup.attributes("-topmost", True)

        x = event.x_root + 10
        y = event.y_root + 10
        self.norm_popup.geometry(f"+{x}+{y}")

        bg = "#2b2c2f" if self.dark_mode else "#ffffff"
        fg = "#e8eaed" if self.dark_mode else "#000000"

        frame = tk.Frame(self.norm_popup, bg=bg, bd=1, relief="solid")
        frame.pack(fill="both", expand=True)

        popup_text = self._popup_text_from_norm(text)

        lbl = tk.Label(
            frame,
            text=popup_text,
            font=("Segoe UI", 9, "bold"),
            bg=bg,
            fg=fg,
            justify="left",
        )
        lbl.pack(padx=10, pady=8)

    def on_norm_drag(self, event):
        if self.norm_popup is not None:
            x = event.x_root + 10
            y = event.y_root + 10
            self.norm_popup.geometry(f"+{x}+{y}")

    def on_norm_release(self, event):
        if self.norm_popup is not None:
            self.norm_popup.destroy()
            self.norm_popup = None

    # ---------------- Ağ İşlemleri ----------------

    def on_generate_network(self):
        self.G = generate_random_network(n_nodes=250, p=0.4)
        self.pos = nx.spring_layout(self.G, seed=42, k=0.25)

        self.selected_node = None
        self.last_path = None
        self.hover_node = None

        nodes = sorted(self.G.nodes())
        values = [str(n) for n in nodes]

        self.source_combo["values"] = values
        self.dest_combo["values"] = values

        if values:
            self.source_var.set(values[0])
            self.dest_var.set(values[-1])

        self._draw_graph()

        self._write_results(
            "Ağ başarıyla oluşturuldu.\n"
            f"Düğüm sayısı: {len(self.G.nodes())}\n"
            f"Kenar sayısı: {len(self.G.edges())}\n\n"
            "Kaynak (S) ve Hedef (D) seçip HESAPLA butonuna basınız.\n"
            "Fareyi bir düğüm üzerine getirdiğinizde, düğüm numarası gösterilir.\n"
        )

    def _create_hover_annot(self):
        self.hover_annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(8, 8),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", fc="#ffd54f", ec="black", lw=0.5),
            fontsize=8,
            color="black",
        )
        self.hover_annot.set_visible(False)

    def _draw_graph(self, path=None):
        if self.G is None or self.pos is None:
            self.canvas.draw_idle()
            return

        self.ax.clear()
        self.ax.set_title("Ağ Topolojisi (N ≈ 250)")
        self.ax.axis("off")

        node_color = getattr(self, "current_node_color", self.light_node_color)
        edge_color = getattr(self, "current_edge_color", self.light_edge_color)
        edge_alpha = getattr(self, "current_edge_alpha", 0.15)

        nx.draw_networkx_nodes(
            self.G,
            pos=self.pos,
            ax=self.ax,
            node_size=18,
            node_color=node_color,
            alpha=0.9,
        )

        nx.draw_networkx_edges(
            self.G,
            pos=self.pos,
            ax=self.ax,
            width=0.2,
            edge_color=edge_color,
            alpha=edge_alpha,
        )

        if path is not None and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))

            nx.draw_networkx_edges(
                self.G,
                pos=self.pos,
                edgelist=path_edges,
                ax=self.ax,
                width=3.0,
                edge_color="red",
            )
            nx.draw_networkx_nodes(
                self.G,
                pos=self.pos,
                nodelist=path,
                ax=self.ax,
                node_size=60,
                node_color="red",
            )

        if self.selected_node is not None and self.selected_node in self.G.nodes():
            nx.draw_networkx_nodes(
                self.G,
                pos=self.pos,
                nodelist=[self.selected_node],
                ax=self.ax,
                node_size=80,
                node_color="#ffd54f",
                edgecolors="black",
                linewidths=1.5,
            )

        self._create_hover_annot()

        self.canvas.draw_idle()

    def _write_results(self, text):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state=tk.DISABLED)

    # ---------------- Hover & Click على الرسم ----------------

    def _nearest_node(self, x, y):
        if self.G is None or self.pos is None:
            return None, None
        min_dist = None
        closest = None
        for node, (nx_x, nx_y) in self.pos.items():
            dx = x - nx_x
            dy = y - nx_y
            dist = dx * dx + dy * dy
            if min_dist is None or dist < min_dist:
                min_dist = dist
                closest = node
        return closest, min_dist

    def on_canvas_hover(self, event):
        if self.G is None or self.pos is None:
            return
        if event.inaxes != self.ax:
            if self.hover_annot is not None and self.hover_annot.get_visible():
                self.hover_annot.set_visible(False)
                self.canvas.draw_idle()
            return
        if event.xdata is None or event.ydata is None:
            return

        node, dist = self._nearest_node(event.xdata, event.ydata)
        if dist is not None and dist < 0.01:
            if node != self.hover_node:
                self.hover_node = node
                self.hover_annot.xy = self.pos[node]
                self.hover_annot.set_text(str(node))
                self.hover_annot.set_visible(True)
                self.canvas.draw_idle()
        else:
            if self.hover_annot is not None and self.hover_annot.get_visible():
                self.hover_node = None
                self.hover_annot.set_visible(False)
                self.canvas.draw_idle()

    def on_canvas_click(self, event):
        if self.G is None or self.pos is None:
            return
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        node, dist = self._nearest_node(event.xdata, event.ydata)
        if dist is not None and dist < 0.01:
            self.selected_node = node
            self._draw_graph(path=self.last_path)

    # ---------------- Algoritma Koşma ----------------

    def run_genetic_algorithm(self, G, s, d, w_delay, w_rel, w_res):
        """
        TODO (Grup 1):
        Buraya Genetik Algoritma ile en iyi yolu bulan kod eklenecek.
        Şimdilik sadece bilgilendirme veriyoruz.
        """
        messagebox.showinfo(
            "Bilgi",
            "Genetik Algoritma versiyonu henüz eklenmedi.\n"
            "Bu kısım Grup 1 tarafından doldurulacak.",
        )
        return None

    def run_ant_colony(self, G, s, d, w_delay, w_rel, w_res):
        """
        TODO (Grup 1):
        Buraya Karınca Kolonisi Algoritması (ACO) ile yol bulma kodu gelecek.
        """
        messagebox.showinfo(
            "Bilgi",
            "Karınca Kolonisi Algoritması henüz eklenmedi.\n"
            "Bu kısım Grup 1 tarafından doldurulacak.",
        )
        return None

    def run_q_learning(self, G, s, d, w_delay, w_rel, w_res):
        """
        TODO (Grup 2):
        Buraya Q-Learning (Pekiştirmeli Öğrenme) ile yol bulma kodu gelecek.
        """
        messagebox.showinfo(
            "Bilgi",
            "Q-Learning (RL) algoritması henüz eklenmedi.\n"
            "Bu kısım Grup 2 tarafından doldurulacak.",
        )
        return None

    # ---------------- HESAPLA Butonu ----------------

    def on_compute(self):
        if self.G is None:
            messagebox.showwarning("Uyarı", "Lütfen önce 'Ağı Oluştur' butonuna basınız.")
            return

        try:
            s = int(self.source_var.get())
            d = int(self.dest_var.get())
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçersiz kaynak/hedef düğüm seçimi.")
            return

        if s not in self.G.nodes or d not in self.G.nodes:
            messagebox.showwarning("Uyarı", "Seçilen S veya D ağda bulunamadı.")
            return

        d_raw = self.w_delay.get()
        r_raw = self.w_rel.get()
        s_raw = self.w_res.get()
        total = d_raw + r_raw + s_raw

        if total == 0:
            messagebox.showwarning(
                "Uyarı", "Ağırlıklar sıfır olamaz. Lütfen sliderları ayarlayınız."
            )
            return

        w_delay = d_raw / total
        w_rel = r_raw / total
        w_res = s_raw / total

        alg = self.alg_var.get()

        if alg.startswith("Basit"):
            path = find_best_path_simple(self.G, s, d, w_delay, w_rel, w_res)
        elif alg.startswith("Genetik"):
            path = self.run_genetic_algorithm(self.G, s, d, w_delay, w_rel, w_res)
        elif alg.startswith("Karınca"):
            path = self.run_ant_colony(self.G, s, d, w_delay, w_rel, w_res)
        elif alg.startswith("Q-Learning"):
            path = self.run_q_learning(self.G, s, d, w_delay, w_rel, w_res)
        else:
            messagebox.showwarning("Uyarı", "Bilinmeyen algoritma seçimi.")
            return

        if path is None:
            return  # mesajlar yukarıda verildi

        self.last_path = path

        total_delay = compute_total_delay(self.G, path)
        rel_cost = compute_reliability_cost(self.G, path)
        res_cost = compute_resource_cost(self.G, path)
        total_cost = compute_total_cost(
            total_delay, rel_cost, res_cost, w_delay, w_rel, w_res
        )

        self._draw_graph(path=path)

        out = []
        out.append(f"Seçilen Algoritma: {alg}\n\n")
        out.append(f"En İyi Yol (düğümler):\n{path}\n\n")
        out.append(f"Toplam Gecikme (ms): {total_delay:.4f}\n")
        out.append(f"Güvenilirlik Maliyeti: {rel_cost:.4f}\n")
        out.append(f"Kaynak Maliyeti: {res_cost:.4f}\n")
        out.append(f"Toplam Maliyet: {total_cost:.4f}\n\n")
        out.append("Normalize Edilmiş Ağırlıklar (toplam=1):\n")
        out.append(
            f"Wdelay={w_delay:.2f}, Wrel={w_rel:.2f}, Wres={w_res:.2f}\n"
        )

        self._write_results("".join(out))


# ======================================================
# Program giriş noktası
# ======================================================

if __name__ == "__main__":
    app = QoSRoutingApp()
    app.mainloop()
