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
# 3) GUI Uygulaması + ANİMASYON (PROFESSIONAL EDITION)
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
        self.base_pos = None      # layout: Spring (Original)
        self.pos = None           # layout: Current (Animation/Morph)
        self.selected_node = None
        self.last_path = None
        self.hover_node = None
        
        # Animation State
        self.anim_phase = 0.0
        self.anim_speed = 0.15  # Slower, smoother spin
        self.is_morphing = False
        self.morph_progress = 0.0  # 0.0 = Column, 1.0 = Spring
        self.morph_duration = 90   # Frames for transition (1.5s @ 60fps)

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
        s.configure("Card.TLabelframe", 
                    background=self.col_bg_panel, 
                    borderwidth=1, 
                    relief="solid",
                    bordercolor=self.col_border)
        s.configure("Card.TLabelframe.Label",
                    background=self.col_bg_panel,
                    foreground=self.col_accent,
                    font=("Segoe UI", 9, "bold"))

        # Labels
        s.configure("TLabel", background=self.col_bg_panel, foreground=self.col_text_main, font=("Segoe UI", 9))
        s.configure("Dim.TLabel", background=self.col_bg_panel, foreground=self.col_text_dim, font=("Segoe UI", 8))

        # Buttons (Flat, Modern)
        s.configure("Accent.TButton",
                    font=("Segoe UI", 10, "bold"),
                    background=self.col_accent, 
                    foreground="white", 
                    borderwidth=0,
                    padding=10)
        s.map("Accent.TButton", 
              background=[("active", self.col_accent_hover), ("pressed", "#0284c7")])

        # Scales
        s.configure("Modern.Horizontal.TScale",
                    troughcolor="#1e293b",
                    background=self.col_bg_panel,
                    sliderlength=20,
                    sliderthickness=6)

    # ---------------- UI Layout ----------------

    def _build_layout(self):
        # Main Container
        container = ttk.Frame(self, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        # Left: Visualization (The Energy Column)
        left_panel = ttk.Frame(container, style="Main.TFrame")
        left_panel.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("off")
        
        # Match Figure background to App background
        self.fig.patch.set_facecolor(self.mpl_bg)
        self.ax.set_facecolor(self.mpl_bg)

        self.canvas = FigureCanvasTkAgg(self.fig, left_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Events
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.canvas.mpl_connect("button_press_event", self.on_click)

        # Right: Controls (Sidebar)
        right_panel = ttk.Frame(container, width=380, style="Panel.TFrame")
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        # Header
        header = ttk.Frame(right_panel, style="Panel.TFrame", padding=25)
        header.pack(fill="x")
        ttk.Label(header, text="QoS ROUTING", font=("Segoe UI", 20, "bold"), foreground="white").pack(anchor="w")
        ttk.Label(header, text="OPTIMIZATION ENGINE V2.0", style="Dim.TLabel").pack(anchor="w")

        # Separator
        ttk.Frame(right_panel, height=1, style="Panel.TFrame", cursor="arrow").pack(fill="x", padx=25, pady=5)

        # Controls Container
        controls = ttk.Frame(right_panel, style="Panel.TFrame", padding=25)
        controls.pack(fill="both", expand=True)

        # 1. Network Generation
        card_gen = ttk.LabelFrame(controls, text="TOPOLOGY", style="Card.TLabelframe", padding=15)
        card_gen.pack(fill="x", pady=(0, 20))
        
        ttk.Button(card_gen, text="INITIALIZE NETWORK", style="Accent.TButton", command=self.on_generate).pack(fill="x")

        # 2. Pathfinding
        card_path = ttk.LabelFrame(controls, text="ROUTING PARAMETERS", style="Card.TLabelframe", padding=15)
        card_path.pack(fill="x", pady=(0, 20))

        grid_frame = ttk.Frame(card_path, style="Panel.TFrame")
        grid_frame.pack(fill="x", pady=5)
        
        ttk.Label(grid_frame, text="SOURCE").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(grid_frame, text="TARGET").grid(row=0, column=1, sticky="w", pady=2)
        
        self.s_var = tk.StringVar()
        self.d_var = tk.StringVar()
        self.s_combo = ttk.Combobox(grid_frame, textvariable=self.s_var, state="readonly", width=12)
        self.d_combo = ttk.Combobox(grid_frame, textvariable=self.d_var, state="readonly", width=12)
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
            ttk.Scale(f, from_=0, to=10, variable=var, style="Modern.Horizontal.TScale").pack(fill="x", pady=(5,0))

        add_slider(card_path, "Latency Priority", self.w_delay)
        add_slider(card_path, "Reliability Priority", self.w_rel)
        add_slider(card_path, "Resource Priority", self.w_res)

        # Compute Button
        ttk.Button(card_path, text="COMPUTE OPTIMAL PATH", style="Accent.TButton", command=self.on_compute).pack(fill="x", pady=(20, 0))

        # 3. Logs
        card_log = ttk.LabelFrame(controls, text="SYSTEM LOG", style="Card.TLabelframe", padding=10)
        card_log.pack(fill="both", expand=True)
        
        self.out = tk.Text(card_log, wrap="word", font=("Consolas", 9), 
                           bg="#050505", fg="#0ea5e9", relief="flat", highlightthickness=0)
        self.out.pack(fill="both", expand=True)

    # ---------------- LOGIC ----------------

    def on_generate(self):
        self.G = generate_random_network()
        self.base_pos = nx.spring_layout(self.G, seed=42, k=0.3) # Standard layout
        self.pos = dict(self.base_pos)
        
        # Reset Animation State
        self.is_morphing = False
        self.morph_progress = 0.0
        self.last_path = None
        
        # Populate Combos
        nodes = sorted(self.G.nodes())
        vals = [str(n) for n in nodes]
        self.s_combo["values"] = vals
        self.d_combo["values"] = vals
        if vals:
            self.s_var.set(vals[0])
            self.d_var.set(vals[-1])

        self.log("Network Initialized.\nNodes: {}\nEdges: {}".format(len(nodes), len(self.G.edges())))

    def on_compute(self):
        if not self.G: return
        
        # Trigger Morph
        self.is_morphing = True
        self.morph_progress = 0.0
        
        # Calculate Path (Logic)
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
                    w_d, w_r, w_res
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

        # 1. Update Phase
        self.anim_phase += self.anim_speed
        
        # 2. Handle Morphing
        if self.is_morphing:
            self.morph_progress += (1.0 / self.morph_duration)
            if self.morph_progress >= 1.0:
                self.morph_progress = 1.0
                # Stop morphing, stay in Spring layout
        
        # 3. Calculate Positions
        self.update_positions()
        
        # 4. Draw
        self.draw()
        
        self.after(20, self.animate_step)

    def update_positions(self):
        # Target 1: Energy Column (The "Tornado" / Beam)
        col_pos = self.calculate_column_positions()
        
        # Target 2: Spring Layout (Base)
        spring_pos = self.base_pos
        
        # Interpolate
        t = self.ease_in_out(self.morph_progress)
        
        new_pos = {}
        for n in self.G.nodes():
            x1, y1 = col_pos[n]
            x2, y2 = spring_pos[n]
            
            # Linear Interpolation (Lerp)
            nx_ = x1 + (x2 - x1) * t
            ny_ = y1 + (y2 - y1) * t
            new_pos[n] = (nx_, ny_)
            
        self.pos = new_pos

    def calculate_column_positions(self):
        """
        Generates the 'Energy Column' positions.
        Vertical cylinder with slight hourglass shape, fast spin.
        """
        xs = [p[0] for p in self.base_pos.values()]
        ys = [p[1] for p in self.base_pos.values()]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        
        # Normalize heights
        min_y, max_y = min(ys), max(ys)
        height_span = max(max_y - min_y, 1e-6)
        
        res = {}
        for n, (x0, y0) in self.base_pos.items():
            # Original radial properties
            dx = x0 - cx
            dy = y0 - cy
            
            # Normalized height (0..1)
            h = (y0 - min_y) / height_span
            
            # Radius: Hourglass shape
            # Narrow in middle (h=0.5), wider at ends
            base_r = 0.15  # Base width
            waist_factor = 1.0 + 1.5 * ((h - 0.5) ** 2) # 1.0 at center, 1.375 at ends
            r = base_r * waist_factor
            
            # Angle: Fast spin + vertical twist
            # Spin speed depends on height to create "shearing" energy effect
            angle_offset = self.anim_phase * (0.1 + 0.05 * h) 
            original_angle = math.atan2(dy, dx)
            angle = original_angle + angle_offset
            
            # Final Position
            nx_ = cx + r * math.cos(angle)
            ny_ = cy + r * math.sin(angle) * 2.5 # Stretch vertically
            
            res[n] = (nx_, ny_)
            
        return res

    def ease_in_out(self, t):
        # Cubic easing
        return t * t * (3 - 2 * t)

    # ---------------- RENDERING ----------------

    def draw(self):
        self.ax.clear()
        self.ax.axis("off")
        
        # Background is already set in __init__, but ensure it stays
        self.fig.patch.set_facecolor(self.mpl_bg)
        self.ax.set_facecolor(self.mpl_bg)

        if not self.pos: return

        # Extract coordinates
        x_vals = [p[0] for p in self.pos.values()]
        y_vals = [p[1] for p in self.pos.values()]
        
        # 1. Draw Edges (Faint, only if morphing or static)
        # In full column mode, edges might clutter, but let's keep them very faint
        edge_alpha = 0.02 + 0.15 * self.morph_progress # More visible when flat
        if edge_alpha > 0.01:
            nx.draw_networkx_edges(
                self.G, self.pos, ax=self.ax,
                width=0.5, edge_color="#334155", alpha=edge_alpha
            )

        # 2. Draw Nodes (The Glow Effect)
        # We use scatter for better control
        
        # Layer 3: Outer Halo (Large, Faint Blue)
        self.ax.scatter(x_vals, y_vals, s=250, c=self.mpl_node_glow2, alpha=0.08, zorder=1, linewidths=0)
        
        # Layer 2: Inner Glow (Medium, Cyan)
        self.ax.scatter(x_vals, y_vals, s=80, c=self.mpl_node_glow1, alpha=0.4, zorder=2, linewidths=0)
        
        # Layer 1: Core (Small, White/Bright)
        # Add a "sparkle" effect based on phase
        sizes = [15 + 8 * math.sin(self.anim_phase + i*0.1) for i in range(len(x_vals))]
        self.ax.scatter(x_vals, y_vals, s=sizes, c=self.mpl_node_core, alpha=0.95, zorder=3, linewidths=0)

        # 3. Draw Path (If exists)
        if self.last_path and self.morph_progress > 0.9:
            path_edges = list(zip(self.last_path[:-1], self.last_path[1:]))
            
            # Draw Path Edges (Neon)
            nx.draw_networkx_edges(
                self.G, self.pos, ax=self.ax,
                edgelist=path_edges, width=2.5, edge_color=self.col_accent, alpha=0.9
            )
            
            # Draw Path Nodes
            path_pos = {n: self.pos[n] for n in self.last_path}
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=self.last_path, node_size=50, node_color="#ffffff"
            )

        # 4. Highlight Selection
        if self.selected_node is not None:
             x, y = self.pos[self.selected_node]
             self.ax.scatter([x], [y], s=300, c="#f59e0b", alpha=0.5, zorder=4)

        self.canvas.draw_idle()

    # ---------------- INTERACTION ----------------

    def on_hover(self, event):
        if event.xdata is None: return
        # Simple nearest neighbor
        # (Optimization: could use KDTree but N=250 is small enough)
        pass 

    def on_click(self, event):
        if event.xdata is None: return
        # Find nearest
        min_d = float("inf")
        target = None
        for n, (x, y) in self.pos.items():
            d = (x - event.xdata)**2 + (y - event.ydata)**2
            if d < min_d:
                min_d = d
                target = n
        
        if target is not None and min_d < 0.05: # Threshold
            self.selected_node = target
            self.log(f"Selected Node: {target}")


if __name__ == "__main__":
    app = QoSRoutingApp()
    app.mainloop()
