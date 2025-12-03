import tkinter as tk
from tkinter import ttk, messagebox
import random
import math

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


# ======================================================
# 1) Ağ Oluşturma ve Metrik Hesaplama Fonksiyonları
# ======================================================

def generate_random_network(n_nodes=250, p=0.4):
    G = nx.erdos_renyi_graph(n_nodes, p)

    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    for node in G.nodes():
        G.nodes[node]["processing_delay"] = random.uniform(0.5, 2.0)
        G.nodes[node]["node_reliability"] = random.uniform(0.95, 0.999)

    for u, v in G.edges():
        G.edges[u, v]["bandwidth"] = random.uniform(100, 1000)
        G.edges[u, v]["link_delay"] = random.uniform(3, 15)
        G.edges[u, v]["link_reliability"] = random.uniform(0.95, 0.999)

    return G


def compute_total_delay(G, path):
    if len(path) < 2:
        return 0.0

    link_delay_sum = sum(
        G.edges[path[i], path[i + 1]]["link_delay"] for i in range(len(path) - 1)
    )
    processing_sum = sum(G.nodes[node]["processing_delay"] for node in path[1:-1])
    return link_delay_sum + processing_sum


def compute_reliability_cost(G, path):
    if len(path) == 0:
        return float("inf")

    rel_cost = 0.0

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        rel_cost += -math.log(G.edges[u, v]["link_reliability"])
        rel_cost += -math.log(G.nodes[u]["node_reliability"])
        rel_cost += -math.log(G.nodes[v]["node_reliability"])

    return rel_cost


def compute_resource_cost(G, path, max_bw=1000.0):
    if len(path) < 2:
        return float("inf")

    return sum(
        max_bw / G.edges[path[i], path[i + 1]]["bandwidth"]
        for i in range(len(path) - 1)
    )


def compute_total_cost(delay, rel_cost, res_cost, w_delay, w_rel, w_res):
    return w_delay * delay + w_rel * rel_cost + w_res * res_cost


def find_best_path_simple(G, s, d, w_delay, w_rel, w_res):
    """Basit çok amaçlı ağırlıklarla Dijkstra benzeri yol bulma."""
    if s == d:
        return [s]

    def edge_weight(u, v, data):
        link_delay = data["link_delay"]
        proc_delay = G.nodes[v]["processing_delay"]

        edge_rel_cost = (
            -math.log(data["link_reliability"])
            - math.log(G.nodes[u]["node_reliability"])
            - math.log(G.nodes[v]["node_reliability"])
        )

        res_cost = 1000.0 / data["bandwidth"]
        total_edge_delay = link_delay + proc_delay

        return compute_total_cost(
            total_edge_delay, edge_rel_cost, res_cost, w_delay, w_rel, w_res
        )

    try:
        return nx.dijkstra_path(
            G, s, d, weight=lambda u, v, d: edge_weight(u, v, d)
        )
    except nx.NetworkXNoPath:
        return None


# ======================================================
# 3) GUI Uygulaması + ANİMASYON (OPTIMIZED)
# ======================================================

class QoSRoutingApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("QoS Routing - Professional Edition")
        self.geometry("1400x850")
        try:
            self.state("zoomed")
        except:
            pass

        self.dark_mode = True

        self.G = None
        self.base_pos = None      # Spring layout
        self.pos = None           # Current positions
        self.node_list = []
        self.edge_list = []
        self.selected_node = None
        self.last_path = None
        self.hover_node = None

        # Animation State
        self.anim_phase = 0.0
        self.anim_speed = 1.0      # أسرع دوران
        self.is_morphing = False
        self.morph_progress = 0.0  # 0.0 = Tornado, 1.0 = Spring
        self.morph_duration = 60   # ~1.2s (أسرع من قبل بكثير)

        # Matplotlib artists (نرسم مرة وحدة ثم نحدّث)
        self.art_edges = None
        self.art_glow_outer = None
        self.art_glow_inner = None
        self.art_core = None
        self.art_path_edges = None
        self.art_path_nodes = None
        self.art_selection = None

        self._init_styles()
        self._build_layout()

        # Start Animation Loop
        self.after(20, self.animate_step)

    # ---------------- Styles (Professional / Deep Space) ----------------

    def _init_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except:
            pass

        # Palette: Deep Space / Energy
        self.col_bg_main = "#000000"     # Pure Black
        self.col_bg_panel = "#050505"    # Almost Black
        self.col_accent = "#0ea5e9"      # Sky Blue
        self.col_accent_hover = "#38bdf8"
        self.col_text_main = "#f8fafc"
        self.col_text_dim = "#64748b"
        self.col_border = "#1e293b"

        # Matplotlib Colors
        self.mpl_bg = self.col_bg_main
        self.mpl_node_core = "#ffffff"   # White core
        self.mpl_node_glow1 = "#0ea5e9"  # Cyan inner
        self.mpl_node_glow2 = "#3b82f6"  # Blue outer

        s = self.style

        # Frames
        s.configure("Main.TFrame", background=self.col_bg_main)
        s.configure("Panel.TFrame", background=self.col_bg_panel)

        # Cards (LabelFrames)
        s.configure(
            "Card.TLabelframe",
            background=self.col_bg_panel,
            borderwidth=1,
            relief="solid",
            bordercolor=self.col_border,
        )
        s.configure(
            "Card.TLabelframe.Label",
            background=self.col_bg_panel,
            foreground=self.col_accent,
            font=("Segoe UI", 9, "bold"),
        )

        # Labels
        s.configure(
            "TLabel",
            background=self.col_bg_panel,
            foreground=self.col_text_main,
            font=("Segoe UI", 9),
        )
        s.configure(
            "Dim.TLabel",
            background=self.col_bg_panel,
            foreground=self.col_text_dim,
            font=("Segoe UI", 8),
        )

        # Buttons
        s.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.col_accent,
            foreground="white",
            borderwidth=0,
            padding=10,
        )
        s.map(
            "Accent.TButton",
            background=[("active", self.col_accent_hover), ("pressed", "#0284c7")],
        )

        # Scales
        s.configure(
            "Modern.Horizontal.TScale",
            troughcolor="#1e293b",
            background=self.col_bg_panel,
            sliderlength=20,
            sliderthickness=6,
        )

    # ---------------- UI Layout ----------------

    def _build_layout(self):
        # Main Container
        container = ttk.Frame(self, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        # Left: Visualization
        left_panel = ttk.Frame(container, style="Main.TFrame")
        left_panel.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("off")

        self.fig.patch.set_facecolor(self.mpl_bg)
        self.ax.set_facecolor(self.mpl_bg)

        self.canvas = FigureCanvasTkAgg(self.fig, left_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Events
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.canvas.mpl_connect("button_press_event", self.on_click)

        # Right: Controls
        right_panel = ttk.Frame(container, width=380, style="Panel.TFrame")
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        # Header
        header = ttk.Frame(right_panel, style="Panel.TFrame", padding=25)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="QoS ROUTING",
            font=("Segoe UI", 20, "bold"),
            foreground="white",
        ).pack(anchor="w")
        ttk.Label(
            header, text="OPTIMIZATION ENGINE V2.0", style="Dim.TLabel"
        ).pack(anchor="w")

        ttk.Frame(right_panel, height=1, style="Panel.TFrame").pack(
            fill="x", padx=25, pady=5
        )

        controls = ttk.Frame(right_panel, style="Panel.TFrame", padding=25)
        controls.pack(fill="both", expand=True)

        # 1. Network Generation
        card_gen = ttk.LabelFrame(
            controls, text="TOPOLOGY", style="Card.TLabelframe", padding=15
        )
        card_gen.pack(fill="x", pady=(0, 20))

        ttk.Button(
            card_gen,
            text="INITIALIZE NETWORK",
            style="Accent.TButton",
            command=self.on_generate,
        ).pack(fill="x")

        # 2. Pathfinding
        card_path = ttk.LabelFrame(
            controls,
            text="ROUTING PARAMETERS",
            style="Card.TLabelframe",
            padding=15,
        )
        card_path.pack(fill="x", pady=(0, 20))

        grid_frame = ttk.Frame(card_path, style="Panel.TFrame")
        grid_frame.pack(fill="x", pady=5)

        ttk.Label(grid_frame, text="SOURCE").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(grid_frame, text="TARGET").grid(row=0, column=1, sticky="w", pady=2)

        self.s_var = tk.StringVar()
        self.d_var = tk.StringVar()
        self.s_combo = ttk.Combobox(
            grid_frame, textvariable=self.s_var, state="readonly", width=12
        )
        self.d_combo = ttk.Combobox(
            grid_frame, textvariable=self.d_var, state="readonly", width=12
        )
        self.s_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.d_combo.grid(row=1, column=1, sticky="ew", padx=(0, 0))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Sliders
        self.w_delay = tk.DoubleVar(value=5)
        self.w_rel = tk.DoubleVar(value=3)
        self.w_res = tk.DoubleVar(value=2)

        def add_slider(parent, label, var):
            f = ttk.Frame(parent, style="Panel.TFrame")
            f.pack(fill="x", pady=10)
            ttk.Label(f, text=label.upper(), style="Dim.TLabel").pack(anchor="w")
            ttk.Scale(
                f, from_=0, to=10, variable=var, style="Modern.Horizontal.TScale"
            ).pack(fill="x", pady=(5, 0))

        add_slider(card_path, "Latency Priority", self.w_delay)
        add_slider(card_path, "Reliability Priority", self.w_rel)
        add_slider(card_path, "Resource Priority", self.w_res)

        ttk.Button(
            card_path,
            text="COMPUTE OPTIMAL PATH",
            style="Accent.TButton",
            command=self.on_compute,
        ).pack(fill="x", pady=(20, 0))

        # 3. Logs
        card_log = ttk.LabelFrame(
            controls, text="SYSTEM LOG", style="Card.TLabelframe", padding=10
        )
        card_log.pack(fill="both", expand=True)

        self.out = tk.Text(
            card_log,
            wrap="word",
            font=("Consolas", 9),
            bg="#050505",
            fg="#0ea5e9",
            relief="flat",
            highlightthickness=0,
        )
        self.out.pack(fill="both", expand=True)

    # ---------------- LOGIC ----------------

    def on_generate(self):
        self.G = generate_random_network()
        self.base_pos = nx.spring_layout(self.G, seed=42, k=0.3)
        self.pos = dict(self.base_pos)

        self.node_list = list(self.G.nodes())
        self.edge_list = list(self.G.edges())

        # Reset Animation State
        self.is_morphing = False
        self.morph_progress = 0.0
        self.last_path = None
        self.selected_node = None

        # Populate Combos
        nodes = sorted(self.G.nodes())
        vals = [str(n) for n in nodes]
        self.s_combo["values"] = vals
        self.d_combo["values"] = vals
        if vals:
            self.s_var.set(vals[0])
            self.d_var.set(vals[-1])

        self.log(
            "Network Initialized.\nNodes: {}\nEdges: {}".format(
                len(nodes), len(self.G.edges())
            )
        )

        # Init artists for the first time
        self.init_artists()

    def on_compute(self):
        if not self.G:
            return

        # Trigger Morph (from tornado to original layout)
        self.is_morphing = True
        self.morph_progress = 0.0

        try:
            s = int(self.s_var.get())
            d = int(self.d_var.get())
            w_d = self.w_delay.get()
            w_r = self.w_rel.get()
            w_res = self.w_res.get()

            path = find_best_path_simple(self.G, s, d, w_d, w_r, w_res)

            if path:
                self.last_path = path
                cost = compute_total_cost(
                    compute_total_delay(self.G, path),
                    compute_reliability_cost(self.G, path),
                    compute_resource_cost(self.G, path),
                    w_d,
                    w_r,
                    w_res,
                )
                self.log(f"Path Found: {path}\nTotal Cost: {cost:.2f}")
            else:
                self.log("No path found.")

        except Exception as e:
            self.log(f"Error: {e}")

    def log(self, text):
        self.out.config(state="normal")
        self.out.delete("1.0", tk.END)
        self.out.insert(tk.END, text)
        self.out.config(state="disabled")

    # ---------------- ANIMATION ENGINE ----------------

    def animate_step(self):
        if not self.G:
            self.after(20, self.animate_step)
            return

        # Phase for sparkle + rotation
        self.anim_phase += self.anim_speed

        # Morph progress (رجوع سريع أقل من ثانيتين تقريباً)
        if self.is_morphing:
            self.morph_progress += (1.0 / self.morph_duration)
            if self.morph_progress >= 1.0:
                self.morph_progress = 1.0
                self.is_morphing = False

        # Update positions and artists
        self.update_positions()
        self.update_artists()

        self.after(20, self.animate_step)

    def update_positions(self):
        if not self.base_pos:
            return

        col_pos = self.calculate_column_positions()
        spring_pos = self.base_pos
        t = self.ease_in_out(self.morph_progress)

        new_pos = {}
        for n in self.G.nodes():
            x1, y1 = col_pos[n]
            x2, y2 = spring_pos[n]
            nx_ = x1 + (x2 - x1) * t
            ny_ = y1 + (y2 - y1) * t
            new_pos[n] = (nx_, ny_)
        self.pos = new_pos

    def calculate_column_positions(self):
        xs = [p[0] for p in self.base_pos.values()]
        ys = [p[1] for p in self.base_pos.values()]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)

        min_y, max_y = min(ys), max(ys)
        height_span = max(max_y - min_y, 1e-6)

        res = {}
        for n, (x0, y0) in self.base_pos.items():
            dx = x0 - cx
            dy = y0 - cy

            h = (y0 - min_y) / height_span  # 0..1

            # مخروط (أسفل أضيق، أعلى أوسع)
            base_r = 0.12
            r = base_r * (0.5 + 1.2 * h)

            # دوران سريع مع فرق حسب الارتفاع (شكل إعصار)
            angle_offset = self.anim_phase * (0.2 + 0.1 * h)
            original_angle = math.atan2(dy, dx)
            angle = original_angle + angle_offset

            nx_ = cx + r * math.cos(angle)
            ny_ = cy + r * math.sin(angle) * 2.0

            res[n] = (nx_, ny_)

        return res

    def ease_in_out(self, t):
        return t * t * (3 - 2 * t)

    # ---------------- RENDERING (OPTIMIZED) ----------------

    def init_artists(self):
        """Create Matplotlib artists once فقط."""
        self.ax.clear()
        self.ax.axis("off")
        self.ax.set_facecolor(self.mpl_bg)

        if not self.pos:
            return

        coords = [self.pos[n] for n in self.node_list]
        x_vals = [c[0] for c in coords]
        y_vals = [c[1] for c in coords]

        # Edges
        self.art_edges = nx.draw_networkx_edges(
            self.G,
            self.pos,
            ax=self.ax,
            edgelist=self.edge_list,
            width=0.5,
            edge_color="#334155",
            alpha=0.05,
        )

        # Outer glow
        self.art_glow_outer = self.ax.scatter(
            x_vals,
            y_vals,
            s=250,
            c=self.mpl_node_glow2,
            alpha=0.08,
            zorder=1,
            linewidths=0,
        )

        # Inner glow
        self.art_glow_inner = self.ax.scatter(
            x_vals,
            y_vals,
            s=80,
            c=self.mpl_node_glow1,
            alpha=0.4,
            zorder=2,
            linewidths=0,
        )

        # Core dots
        self.art_core = self.ax.scatter(
            x_vals,
            y_vals,
            s=15,
            c=self.mpl_node_core,
            alpha=0.95,
            zorder=3,
            linewidths=0,
        )

        # Selection marker
        self.art_selection = self.ax.scatter(
            [], [], s=300, c="#f59e0b", alpha=0.5, zorder=4
        )

        self.art_path_edges = None
        self.art_path_nodes = None

        self.canvas.draw()

    def update_artists(self):
        if self.art_core is None or not self.pos:
            return

        coords = [self.pos[n] for n in self.node_list]
        arr = np.array(coords)

        # Update nodes positions
        self.art_glow_outer.set_offsets(arr)
        self.art_glow_inner.set_offsets(arr)
        self.art_core.set_offsets(arr)

        # Update edges
        edge_alpha = 0.02 + 0.15 * self.morph_progress
        if self.art_edges is not None:
            self.art_edges.set_alpha(edge_alpha)
            segments = []
            for u, v in self.edge_list:
                segments.append((self.pos[u], self.pos[v]))
            self.art_edges.set_segments(segments)

        # Sparkle effect
        sizes = [
            15 + 8 * math.sin(self.anim_phase + i * 0.1)
            for i in range(len(self.node_list))
        ]
        self.art_core.set_sizes(sizes)

        # Path drawing (فقط بعد ما يرجع للوضع العادي تقريباً)
        if self.last_path and self.morph_progress > 0.9:
            if self.art_path_edges is None:
                path_edges = list(zip(self.last_path[:-1], self.last_path[1:]))
                self.art_path_edges = nx.draw_networkx_edges(
                    self.G,
                    self.pos,
                    ax=self.ax,
                    edgelist=path_edges,
                    width=2.5,
                    edge_color=self.col_accent,
                    alpha=0.9,
                )
                self.art_path_nodes = nx.draw_networkx_nodes(
                    self.G,
                    self.pos,
                    ax=self.ax,
                    nodelist=self.last_path,
                    node_size=50,
                    node_color="#ffffff",
                )
        else:
            if self.art_path_edges is not None:
                self.art_path_edges.remove()
                self.art_path_edges = None
            if self.art_path_nodes is not None:
                self.art_path_nodes.remove()
                self.art_path_nodes = None

        # Selection highlight
        if self.selected_node is not None and self.selected_node in self.pos:
            x, y = self.pos[self.selected_node]
            self.art_selection.set_offsets([[x, y]])
        else:
            self.art_selection.set_offsets(np.empty((0, 2)))

        self.canvas.draw_idle()

    # ---------------- INTERACTION ----------------

    def on_hover(self, event):
        # حالياً ما نسوي شي في الهوفر (ممكن نضيف تلميع خاص لاحقاً)
        return

    def on_click(self, event):
        if event.xdata is None or event.ydata is None or not self.pos:
            return

        # Pick nearest node (بسرعة، 250 نود فقط)
        min_d = float("inf")
        target = None
        for n, (x, y) in self.pos.items():
            d = (x - event.xdata) ** 2 + (y - event.ydata) ** 2
            if d < min_d:
                min_d = d
                target = n

        # Threshold بسيط
        if target is not None and min_d < 0.05:
            self.selected_node = target
            self.log(f"Selected Node: {target}")

            # مثال: لو تبغى تخلي الكليك يغيّر SOURCE:
            # self.s_var.set(str(target))


if __name__ == "__main__":
    app = QoSRoutingApp()
    app.mainloop()
