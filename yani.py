import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import random
import math


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

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color="#ffffff", corner_radius=15, padding=10, bg=None, **kwargs):
        if bg is None:
            bg = "#f5f5f7" # Default fallback
        super().__init__(parent, borderwidth=0, highlightthickness=0, bg=bg, **kwargs)
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        self.padding = padding
        
        self.inner_frame = ttk.Frame(self)
        # We will configure inner_frame background later or let it inherit if possible, 
        # but ttk frames usually need style. We'll handle this in _apply_theme or init.
        
        self.window_id = self.create_window(0, 0, window=self.inner_frame, anchor="nw")
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self.delete("bg_rect")
        w = event.width
        h = event.height
        r = self.corner_radius
        
        # Create a rounded polygon
        points = [
            (r, 0), (w-r, 0), (w, 0), (w, r),
            (w, h-r), (w, h), (w-r, h), (r, h),
            (0, h), (0, h-r), (0, r), (0, 0)
        ]
        # Smooth polygon is hard in standard tkinter without complex curves. 
        # Alternative: Draw arcs and rectangles.
        
        # Simpler approach for "modern" look: just use the create_polygon with smooth=True? 
        # No, that makes it blobby.
        # Let's use the arc+rect method.
        
        self._draw_rounded_rect(0, 0, w, h, r)
        
        # Resize inner frame
        # Padding determines how far inside the rounded border the content is
        iw = w - 2*self.padding
        ih = h - 2*self.padding
        if iw < 1: iw = 1
        if ih < 1: ih = 1
        
        self.itemconfigure(self.window_id, width=iw, height=ih)
        self.coords(self.window_id, self.padding, self.padding)

    def _draw_rounded_rect(self, x1, y1, x2, y2, r):
        # Top-left
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        # Top-right
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        # Bottom-right
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        # Bottom-left
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        
        # Rectangles
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        
        self.tag_lower("bg_rect")

    def set_bg(self, color):
        self.bg_color = color
        self.inner_frame.configure(style="Card.TFrame") # Helper to ensure style update
        # Trigger redraw
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 1 and h > 1:
            self.delete("bg_rect")
            self._draw_rounded_rect(0, 0, w, h, self.corner_radius)


class QoSRoutingApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("QoS Çok Amaçlı Yönlendirme - GUI Demo")
        self.geometry("1300x760") # Increased height slightly
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
        self.light_bg_side = "#f5f5f7" # Same as main for cleaner look with cards
        self.light_card = "#ffffff"
        self.light_divider = "#ffffff"
        self.light_node_color = "#4a90e2"
        self.light_edge_color = "#bbbbbb"

        self.dark_bg_main = "#202124"
        self.dark_bg_side = "#202124"
        self.dark_card = "#30343a"
        self.dark_divider = "#3c4043"
        self.dark_node_color = "#8ab4f8"
        self.dark_edge_color = "#5f6368"
        
        # Final Aesthetic Colors
        self.navy_bg = "#0a192f"
        self.muted_gray = "#708090"
        
        # Control Panel Colors
        self.navy_card = "#112240"
        self.navy_text = "#e6f1ff"
        self.navy_button = "#1d4ed8"

        self.style = style
        self._init_styles()

        self.G = None
        self.pos = None
        
        self.rounded_frames = [] # Keep track to update colors

        self._build_layout()

    # ---------------- Styles ----------------

    def _init_styles(self):
        s = self.style

        s.configure("Main.TFrame", background=self.light_bg_main)
        s.configure("Card.TFrame", background=self.light_card) # For inner frames

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
        
        # Label styles
        s.configure("TLabel", background=self.light_card, font=("Segoe UI", 9))
        s.configure("Header.TLabel", background=self.light_card, font=("Segoe UI", 11, "bold"))
        s.configure("Small.TLabel", background=self.light_card, font=("Segoe UI", 8))
        
        # Transparent label for main background usage if needed
        s.configure("Main.TLabel", background=self.light_bg_main, font=("Segoe UI", 9))

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
        # Apply Navy Theme regardless of dark_mode flag for the final look
        # But we can keep the logic if we want to support switching back, 
        # however the user request implies a permanent change for this "updated interface design".
        # I will override the "Light" mode defaults with the Navy theme or just set them directly.
        
        bg_main = self.navy_bg
        bg_side = self.navy_bg # Main container bg
        card_bg = self.navy_card
        fg_text = self.navy_text
        divider_bg = "#1e3a8a" # Slightly lighter navy for divider
        graph_bg = self.navy_bg
        
        # Button colors
        btn_bg = self.navy_button
        btn_fg = "#ffffff"

        self.configure(bg=bg_main)
        self.style.configure("Main.TFrame", background=bg_main)
        self.style.configure("Side.TFrame", background=bg_side)
        self.style.configure("Card.TLabelframe", background=card_bg, foreground=fg_text)
        self.style.configure("Card.TLabelframe.Label", background=card_bg, foreground=fg_text)
        self.style.configure("Card.TFrame", background=card_bg)
        
        self.style.configure("TLabel", background=card_bg, foreground=fg_text)
        self.style.configure("Header.TLabel", background=card_bg, foreground=fg_text)
        self.style.configure("Small.TLabel", background=card_bg, foreground=fg_text)
        self.style.configure("Main.TLabel", background=bg_main, foreground=fg_text)
        
        # Update Button Styles
        self.style.configure(
            "Accent.TButton",
            background=btn_bg,
            foreground=btn_fg,
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#2563eb")], # Lighter blue on hover
        )
        
        self.style.configure(
            "Ghost.TButton",
            background=card_bg,
            foreground=fg_text,
        )
        self.style.map(
            "Ghost.TButton",
            background=[("active", self.navy_bg)],
        )

        self.style.configure(
            "Modern.Horizontal.TScale",
            background=card_bg,
            troughcolor="#334155",
        )
        
        # Update RoundedFrames
        for rf in self.rounded_frames:
            rf.set_bg(card_bg)
            rf.configure(bg=bg_main)

        # Update Divider
        self.divider_frame.configure(bg=divider_bg)

        # Update Text widget
        if hasattr(self, 'results_text'):
            self.results_text.config(bg=card_bg, fg=fg_text, insertbackground=fg_text)

        # Update Matplotlib Figure Background
        if hasattr(self, 'fig'):
            self.fig.patch.set_facecolor(graph_bg)
            self.ax.set_facecolor(graph_bg)
        
        # Store current bg for redraws
        self.current_bg_color = graph_bg

        self.current_node_color = self.muted_gray
        self.current_edge_color = "#cccccc"
        self.current_edge_alpha = 0.1

        self._draw_graph(path=self.last_path)

        if self.norm_popup is not None:
            self._style_norm_popup()

    # ---------------- GUI Yapısı ----------------

    def _build_layout(self):
        # Main container
        main_container = ttk.Frame(self, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT SIDE (Visualization) ---
        # We use a RoundedFrame to hold the graph
        self.left_rf = RoundedFrame(main_container, bg_color=self.light_card, corner_radius=20, padding=2, bg=self.light_bg_main)
        self.left_rf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.rounded_frames.append(self.left_rf)
        
        # Inside the rounded frame, we put the canvas
        # Note: FigureCanvasTkAgg creates a widget. We pack it into left_rf.inner_frame
        
        self.fig = Figure(figsize=(6.5, 5.8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Ağ Topolojisi (N ≈ 250)")
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_rf.inner_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("motion_notify_event", self.on_canvas_hover)
        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)
        self.hover_annot = None

        # --- DIVIDER ---
        self.divider_frame = tk.Frame(main_container, bg=self.light_divider, width=2)
        self.divider_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # --- RIGHT SIDE (Controls) ---
        right_container = ttk.Frame(main_container, style="Main.TFrame", width=340)
        right_container.pack(side=tk.RIGHT, fill=tk.Y)
        right_container.pack_propagate(False)

        # Top bar: Dark mode (outside rounded frames, or inside one? Let's put it at top)


        # ---- Ağ Kontrolleri (Card) ----
        network_frame = ttk.LabelFrame(
            right_container,
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

        ttk.Label(sd_frame, text="Kaynak (S):").grid(row=0, column=0, sticky="w", pady=2)
        self.source_var = tk.StringVar()
        
        # Rounded Entry for Source
        rf_source = RoundedFrame(sd_frame, bg_color="#ffffff", corner_radius=10, padding=2, height=26, bg=self.light_card)
        rf_source.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.rounded_frames.append(rf_source)
        
        self.source_entry = ttk.Entry(rf_source.inner_frame, textvariable=self.source_var, width=10, font=("Segoe UI", 9))
        self.source_entry.pack(fill=tk.BOTH, expand=True, padx=3, pady=1)
        # Remove default border of entry if possible or rely on rounded frame
        # ttk Entry usually has a border. We can try to style it or live with it inside the rounded frame.
        # For a "cleaner" look, we might want to remove the border, but standard ttk themes make this hard without custom layout.
        # Let's just pack it inside.

        ttk.Label(sd_frame, text="Hedef (D):").grid(row=1, column=0, sticky="w", pady=2)
        self.dest_var = tk.StringVar()
        
        # Rounded Entry for Dest
        rf_dest = RoundedFrame(sd_frame, bg_color="#ffffff", corner_radius=10, padding=2, height=26, bg=self.light_card)
        rf_dest.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.rounded_frames.append(rf_dest)

        self.dest_entry = ttk.Entry(rf_dest.inner_frame, textvariable=self.dest_var, width=10, font=("Segoe UI", 9))
        self.dest_entry.pack(fill=tk.BOTH, expand=True, padx=3, pady=1)
        sd_frame.columnconfigure(1, weight=1)

        # ---- Algoritma Seçimi (Card) ----
        algo_frame = ttk.LabelFrame(
            right_container,
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
        
        # Icon Buttons Container
        btn_frame = ttk.Frame(algo_frame, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=4)
        
        self.algo_buttons = {}
        
        # Icons and Labels
        algo_data = [
            ("⚡", "Basit", self.algorithms[0]),
            ("🧬", "Genetik", self.algorithms[1]),
            ("🐜", "Karınca", self.algorithms[2]),
            ("🧠", "Q-Learn", self.algorithms[3]),
        ]
        
        for i, (icon, label, full_name) in enumerate(algo_data):
            btn = ttk.Button(
                btn_frame,
                text=f"{icon} {label}",
                style="Ghost.TButton",
                command=lambda name=full_name: self._select_algorithm(name)
            )
            # 2x2 Grid Layout
            row = i // 2
            col = i % 2
            btn.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            self.algo_buttons[full_name] = btn
            
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
            
        # Select default
        self._select_algorithm(self.algorithms[0])

        ttk.Label(
            algo_frame,
            text="Not: Şu anda yalnızca 'Basit' algoritma çalışıyor.\n"
                 "Diğerleri Grup 1 ve Grup 2 tarafından eklenecek.",
            style="Small.TLabel",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # ---- Ağırlıklar (Card) ----
        weights_frame = ttk.LabelFrame(
            right_container,
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
            from_=0, to=10, orient=tk.HORIZONTAL,
            variable=self.w_delay, style="Modern.Horizontal.TScale",
        )
        self.slider_delay.pack(fill=tk.X, pady=2)

        ttk.Label(weights_frame, text="Güvenilirlik Ağırlığı (Wrel)").pack(anchor="w")
        self.slider_rel = ttk.Scale(
            weights_frame,
            from_=0, to=10, orient=tk.HORIZONTAL,
            variable=self.w_rel, style="Modern.Horizontal.TScale",
        )
        self.slider_rel.pack(fill=tk.X, pady=2)

        ttk.Label(weights_frame, text="Kaynak Ağırlığı (Wres)").pack(anchor="w")
        self.slider_res = ttk.Scale(
            weights_frame,
            from_=0, to=10, orient=tk.HORIZONTAL,
            variable=self.w_res, style="Modern.Horizontal.TScale",
        )
        self.slider_res.pack(fill=tk.X, pady=2)

        self.weights_sum_label = ttk.Label(
            weights_frame,
            text="",
            style="Small.TLabel",
            wraplength=280,
            justify="left",
        )
        self.weights_sum_label.pack(anchor="w", pady=(6, 2))
        
        self.weights_sum_label.bind("<ButtonPress-1>", self.on_norm_press)
        self.weights_sum_label.bind("<B1-Motion>", self.on_norm_drag)
        self.weights_sum_label.bind("<ButtonRelease-1>", self.on_norm_release)

        self._update_weights_label()
        self.slider_delay.bind("<ButtonRelease-1>", lambda e: self._update_weights_label())
        self.slider_rel.bind("<ButtonRelease-1>", lambda e: self._update_weights_label())
        self.slider_res.bind("<ButtonRelease-1>", lambda e: self._update_weights_label())

        # ---- HESAPLA ----
        self.btn_compute = ttk.Button(
            right_container,
            text="HESAPLA (En İyi Yolu Bul)",
            style="Accent.TButton",
            command=self.on_compute,
        )
        self.btn_compute.pack(fill=tk.X, pady=(0, 15))

        for btn in (self.btn_generate, self.btn_compute):
            btn.bind("<Enter>", lambda e, b=btn: b.state(["active"]))
            btn.bind("<Leave>", lambda e, b=btn: b.state(["!active"]))

        # ---- Sonuçlar (Card) ----
        results_frame = ttk.LabelFrame(
            right_container, text="Sonuçlar", style="Card.TLabelframe", padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(
            results_frame,
            height=10,
            wrap="word",
            font=("Consolas", 9),
            bg="#ffffff",
            relief="flat",
            bd=0,
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.insert(tk.END, "Önce ağı oluşturun, sonra S/D ve ağırlıkları seçin.\n")
        self.results_text.config(state=tk.DISABLED)

        self._apply_theme()

    def _select_algorithm(self, algo_name):
        self.alg_var.set(algo_name)
        
        # Update button styles
        for name, btn in self.algo_buttons.items():
            if name == algo_name:
                btn.configure(style="Accent.TButton")
            else:
                btn.configure(style="Ghost.TButton")

    # ---------------- Theme Toggle ----------------

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
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
        self.G = generate_random_network(n_nodes=251, p=0.4)
        self.pos = nx.spring_layout(self.G, seed=42, k=0.25)

        self.selected_node = None
        self.last_path = None
        self.hover_node = None

        nodes = sorted(self.G.nodes())
        # values = [str(n) for n in nodes] # No longer needed for combobox

        # self.source_combo["values"] = values
        # self.dest_combo["values"] = values

        if nodes:
            self.source_var.set(str(nodes[0]))
            self.dest_var.set(str(nodes[-1]))

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
        # Ensure background persists
        bg_color = getattr(self, "current_bg_color", self.navy_bg)
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        self.ax.axis("off")

        # Default node/edge colors
        node_color = self.muted_gray
        edge_color = "#cccccc"
        edge_alpha = 0.1

        # Draw all nodes (Muted Gray)
        nx.draw_networkx_nodes(
            self.G,
            pos=self.pos,
            ax=self.ax,
            node_size=18,
            node_color=node_color,
            alpha=0.8,
        )

        # Draw all edges (Faint)
        nx.draw_networkx_edges(
            self.G,
            pos=self.pos,
            ax=self.ax,
            width=0.5,
            edge_color=edge_color,
            alpha=edge_alpha,
        )

        # Highlight Path
        if path is not None and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))

            # Edges (White)
            nx.draw_networkx_edges(
                self.G,
                pos=self.pos,
                edgelist=path_edges,
                ax=self.ax,
                width=3.0,
                edge_color="#ffffff",
            )
            
            # Shadows for Key Nodes
            shadow_nodes = path
            nx.draw_networkx_nodes(
                self.G,
                pos=self.pos,
                nodelist=shadow_nodes,
                ax=self.ax,
                node_size=120, # Larger than key nodes
                node_color="black",
                alpha=0.5,
            )

            # Intermediate nodes (Red)
            if len(path) > 2:
                nx.draw_networkx_nodes(
                    self.G,
                    pos=self.pos,
                    nodelist=path[1:-1],
                    ax=self.ax,
                    node_size=300,
                    node_color="red",
                )

            # Source node (Yellow)
            nx.draw_networkx_nodes(
                self.G,
                pos=self.pos,
                nodelist=[path[0]],
                ax=self.ax,
                node_size=300,
                node_color="#ffd54f",
                edgecolors="black",
            )

            # Destination node (Red)
            nx.draw_networkx_nodes(
                self.G,
                pos=self.pos,
                nodelist=[path[-1]],
                ax=self.ax,
                node_size=300,
                node_color="red",
                edgecolors="black",
            )
            
            # Start animation
            self.animate_path(path)

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

    def animate_path(self, path):
        # Stop previous animation if exists
        if hasattr(self, 'anim') and self.anim:
            self.anim.event_source.stop()
        
        # Create interpolation points for smooth animation
        points = []
        steps_per_segment = 20
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            
            for t in range(steps_per_segment):
                alpha = t / steps_per_segment
                x = x1 * (1 - alpha) + x2 * alpha
                y = y1 * (1 - alpha) + y2 * alpha
                points.append((x, y))
        
        # Add final point
        final_node = path[-1]
        points.append(self.pos[final_node])
        
        # Create marker
        self.marker, = self.ax.plot([], [], 'o', color='yellow', markersize=8, markeredgecolor='white', zorder=10)
        
        def init():
            self.marker.set_data([], [])
            return self.marker,
        
        def update(frame):
            if frame < len(points):
                x, y = points[frame]
                self.marker.set_data([x], [y])
                # "Radiation" effect: change size slightly
                s = 8 + 4 * math.sin(frame * 0.5)
                self.marker.set_markersize(s)
            return self.marker,
        
        self.anim = animation.FuncAnimation(
            self.fig, update, frames=len(points),
            init_func=init, interval=30, blit=False, repeat=True
        )
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
