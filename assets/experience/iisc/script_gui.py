import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ──────────────────────────────────────────────
# Shared Data
# ──────────────────────────────────────────────
ABBREVIATIONS = {
    "ConductionBandEnergy": "CBE", "ConductionCurrentDensity": "CCD",
    "DopingConcentration": "DC", "EffectiveIntrinsicDensity": "EID",
    "ElectricField": "EF", "ElectrostaticPotential": "V",
    "EquilibriumPotential": "EP", "ImpactIonization": "II",
    "IntrinsicDensity": "ni", "LatticeTemperature": "Temp",
    "QuasiFermiPotential": "QFP", "SpaceCharge": "SC",
    "ValenceBandEnergy": "VBE", "eAlphaAvalanche": "eAA",
    "eCurrentDensity": "eJ", "eDensity": "eD",
    "eMobility": "eM", "eQuasiFermiPotential": "eQFP",
    "hAlphaAvalanche": "hAA", "hCurrentDensity": "hJ",
    "hDensity": "hD", "hMobility": "hM", "hQuasiFermiPotential": "hQFP"
}
PARAM_OPTIONS = sorted(list(ABBREVIATIONS.keys()))

def get_short_param_string(param_list):
    short_list = [ABBREVIATIONS.get(p, p) for p in param_list]
    return ", ".join(short_list)

def get_axis_mapping(cutplane_axis, cutline_axis):
    if not cutline_axis: return "Distance" 
    all_axes = {"X", "Y", "Z"}
    removed = {cutplane_axis.upper(), cutline_axis.upper()}
    rem_list = list(all_axes - removed)
    return rem_list[0] if rem_list else "Distance"

def get_ortho_axes(plane_axis):
    axes = ["X", "Y", "Z"]
    if plane_axis.upper() in axes:
        axes.remove(plane_axis.upper())
    return f"{axes[0]} {axes[1]}"

# ──────────────────────────────────────────────
# Custom UI Components
# ──────────────────────────────────────────────
class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)
        self._add_placeholder()

    def _clear_placeholder(self, e=None):
        if self.get() == self.placeholder and self['fg'] == self.placeholder_color:
            self.delete(0, "end")
            self.config(fg=self.default_fg_color)

    def _add_placeholder(self, e=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)
            
    def get_valid(self):
        val = self.get()
        if val == self.placeholder and self['fg'] == self.placeholder_color:
            return ""
        return val

class SimpleCheckBoxFrame(ttk.Frame):
    def __init__(self, master, items, columns=3, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.vars = {}
        row = 0; col = 0
        for item in items:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self, text=item, variable=var)
            chk.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            self.vars[item] = var
            col += 1
            if col >= columns:
                col = 0; row += 1
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1)

    def get_checked_items(self):
        return [item for item, var in self.vars.items() if var.get()]

# ──────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────
class TCADGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCAD TCL Generator GUI v19.1 (Fixed)")
        self.root.geometry("1300x950")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=25)

        self.last_tdr_var = tk.StringVar(value="no")

        main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.left_frame = ttk.Frame(main_pane)
        main_pane.add(self.left_frame, minsize=750)

        # Tabs
        self.nb = ttk.Notebook(self.left_frame)
        self.nb.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.nb.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # ─────────────────────────────────────────────────────────────
        # Configuration Frame (Shared for M1 & M2)
        # ─────────────────────────────────────────────────────────────
        self.global_frame = ttk.LabelFrame(self.left_frame, text="Configuration")
        
        # Row 1: Nodes
        r1 = ttk.Frame(self.global_frame); r1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(r1, text="Nodes (CSV):", width=15).pack(side=tk.LEFT)
        self.glob_nodes = PlaceholderEntry(r1, placeholder="e.g. n1299, n1306")
        self.glob_nodes.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 2: Parameters
        r_param = ttk.Frame(self.global_frame); r_param.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(r_param, text="Param Name:", width=15).pack(side=tk.LEFT)
        self.glob_pname = PlaceholderEntry(r_param, width=10, placeholder="e.g. I")
        self.glob_pname.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(r_param, text="Param Values (CSV):").pack(side=tk.LEFT)
        self.glob_pvals = PlaceholderEntry(r_param, placeholder="e.g. 4.3, 4.8 (Match count with Nodes)")
        self.glob_pvals.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Row 3: TDRs
        r2 = ttk.Frame(self.global_frame); r2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(r2, text="TDR Suffixes:", width=15).pack(side=tk.LEFT)
        self.glob_tdrs = PlaceholderEntry(r2, placeholder="e.g. 01, 02")
        self.glob_tdrs.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 4: Base Path
        r3 = ttk.Frame(self.global_frame); r3.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(r3, text="Base File Path:", width=15).pack(side=tk.LEFT)
        self.glob_path = PlaceholderEntry(r3, placeholder="/home/sentaurus/projects/...")
        self.glob_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 5: Options
        r4 = ttk.Frame(self.global_frame); r4.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(r4, text="Include Node Prefix Only (Last TDR)?").pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text="Yes", variable=self.last_tdr_var, value="yes").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(r4, text="No", variable=self.last_tdr_var, value="no").pack(side=tk.LEFT, padx=10)

        self.init_mode1()
        self.init_mode2()
        self.init_mode3()

        # ─────────────────────────────────────────────────────────────
        # Right Side (Output + Top Right Generate Button)
        # ─────────────────────────────────────────────────────────────
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, minsize=400)

        # Header for Right Pane
        r_header = ttk.Frame(right_frame)
        r_header.pack(side=tk.TOP, fill=tk.X, pady=(5,0), padx=5)
        
        ttk.Label(r_header, text="Generated TCL Script:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, anchor='w')
        
        # [FIXED] Button is created BEFORE on_tab_change is called
        self.btn_gen = ttk.Button(r_header, text="GENERATE SCRIPT", command=self.generate_active)
        self.btn_gen.pack(side=tk.RIGHT)

        self.txt_output = tk.Text(right_frame, width=50) 
        self.txt_output.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        btn_box = ttk.Frame(right_frame)
        btn_box.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)
        ttk.Button(btn_box, text="Copy Output", command=self.copy_out).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Save to File", command=self.save_out).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Clear", command=lambda: self.txt_output.delete("1.0", tk.END)).pack(side=tk.RIGHT)

        # [FIXED] Now safe to call because btn_gen exists
        self.on_tab_change(None)

    def on_tab_change(self, event):
        current_tab = self.nb.select()
        if not current_tab: return
        idx = self.nb.index(current_tab)
        
        # Manage Shared Config Visibility
        self.global_frame.pack_forget()
        if idx == 0: 
            self.global_frame.pack(in_=self.tab1, side=tk.TOP, fill=tk.X, padx=5, pady=5, before=self.m1_canvas)
            if hasattr(self, 'btn_gen'): self.btn_gen.config(text="GENERATE MODE 1") 
        elif idx == 1: 
            self.global_frame.pack(in_=self.tab2, side=tk.TOP, fill=tk.X, padx=5, pady=5, before=self.m2_canvas)
            if hasattr(self, 'btn_gen'): self.btn_gen.config(text="GENERATE MODE 2")
        elif idx == 2:
            if hasattr(self, 'btn_gen'): self.btn_gen.config(text="GENERATE MODE 3")

    def generate_active(self):
        """Dispatches generation to the active tab's function."""
        idx = self.nb.index(self.nb.select())
        if idx == 0: self.gen_m1()
        elif idx == 1: self.gen_m2()
        elif idx == 2: self.gen_m3()

    # ──────────────────────────────────────────────
    # Mode 1: 3D Analysis
    # ──────────────────────────────────────────────
    def init_mode1(self):
        self.tab1 = ttk.Frame(self.nb)
        self.nb.add(self.tab1, text="Mode 1: 3D Analysis")
        
        self.m1_canvas = tk.Canvas(self.tab1)
        sb = ttk.Scrollbar(self.tab1, orient="vertical", command=self.m1_canvas.yview)
        sf = ttk.Frame(self.m1_canvas)
        sf.bind("<Configure>", lambda e: self.m1_canvas.configure(scrollregion=self.m1_canvas.bbox("all")))
        self.m1_canvas.create_window((0,0), window=sf, anchor="nw")
        self.m1_canvas.bind('<Configure>', lambda e: self.m1_canvas.itemconfig(self.m1_canvas.create_window((0,0), window=sf, anchor="nw"), width=e.width))
        self.m1_canvas.configure(yscrollcommand=sb.set)
        self.m1_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        f_cut = ttk.LabelFrame(sf, text="Cut Set Configuration")
        f_cut.pack(fill=tk.X, padx=10, pady=5)

        r1 = ttk.Frame(f_cut); r1.pack(fill=tk.X, pady=(5, 2))
        ttk.Label(r1, text="Cut Plane Axis:").pack(side=tk.LEFT)
        self.m1_cp_axis = ttk.Combobox(r1, values=["X", "Y", "Z"], width=5); self.m1_cp_axis.set("X"); self.m1_cp_axis.pack(side=tk.LEFT, padx=(5, 20))
        self.m1_cp_axis.bind("<<ComboboxSelected>>", self.update_m1_dyn)
        ttk.Label(r1, text="Plane Position:").pack(side=tk.LEFT)
        self.m1_cp_pos = PlaceholderEntry(r1, width=15, placeholder="e.g. 0.0"); self.m1_cp_pos.pack(side=tk.LEFT, padx=5)

        r2 = ttk.Frame(f_cut); r2.pack(fill=tk.X, pady=5)
        ttk.Label(r2, text="Cut Type:").pack(side=tk.LEFT)
        self.m1_type = ttk.Combobox(r2, values=["full", "l"], width=5); self.m1_type.set("full"); self.m1_type.pack(side=tk.LEFT, padx=(5, 20))
        self.m1_type.bind("<<ComboboxSelected>>", self.update_m1_dyn)
        self.m1_dyn_frame = ttk.Frame(r2); self.m1_dyn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(f_cut, text="Select Parameters:").pack(anchor='w', padx=5, pady=(10, 0))
        self.m1_params_frame = SimpleCheckBoxFrame(f_cut, PARAM_OPTIONS, columns=3)
        self.m1_params_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(f_cut, text="ADD CUT SET", command=self.add_m1_set).pack(fill=tk.X, padx=50, pady=10)

        f_table_container = ttk.Frame(sf); f_table_container.pack(fill=tk.X, padx=10, pady=5)
        f_header = ttk.Frame(f_table_container); f_header.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(f_header, text="Active Cut Sets:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        self.m1_sets = []
        def clear_m1_table(): self.m1_sets.clear(); [self.m1_tree.delete(i) for i in self.m1_tree.get_children()]
        def del_m1_row():
            sel = self.m1_tree.selection()
            for s in reversed(sel): del self.m1_sets[self.m1_tree.index(s)]; self.m1_tree.delete(s)

        ttk.Button(f_header, text="Clear All", command=clear_m1_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_header, text="Delete Selected", command=del_m1_row).pack(side=tk.RIGHT, padx=2)

        f_tv = ttk.Frame(f_table_container); f_tv.pack(fill=tk.X, expand=True)
        m1_v = ttk.Scrollbar(f_tv, orient="vertical"); m1_h = ttk.Scrollbar(f_tv, orient="horizontal")
        self.m1_tree = ttk.Treeview(f_tv, columns=("Type", "Details", "Params"), show="headings", 
                                    height=3, yscrollcommand=m1_v.set, xscrollcommand=m1_h.set)
        m1_v.config(command=self.m1_tree.yview); m1_h.config(command=self.m1_tree.xview)
        self.m1_tree.heading("Type", text="Type"); self.m1_tree.column("Type", width=60, anchor="center")
        self.m1_tree.heading("Details", text="Cut Details"); self.m1_tree.column("Details", width=250, anchor="w")
        self.m1_tree.heading("Params", text="Parameters"); self.m1_tree.column("Params", width=200, anchor="w")
        m1_v.pack(side=tk.RIGHT, fill=tk.Y); m1_h.pack(side=tk.BOTTOM, fill=tk.X); self.m1_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)

        f_ex = ttk.LabelFrame(sf, text="Export Options")
        f_ex.pack(fill=tk.X, padx=10, pady=5)

        r_ex = ttk.Frame(f_ex)
        r_ex.pack(fill=tk.X, pady=2, padx=5)

        self.m1_enable_export = tk.BooleanVar(value=True)
        ttk.Checkbutton(r_ex, text="Enable CSV Export",
                        variable=self.m1_enable_export).pack(side=tk.LEFT, padx=(0,15))

        self.m1_same = tk.BooleanVar()
        ttk.Checkbutton(r_ex, text="Combine in Same Plot",
                        variable=self.m1_same).pack(side=tk.LEFT)

        self.m1_split = tk.BooleanVar()
        ttk.Checkbutton(r_ex, text="Split CSV by Cut Set",
                        variable=self.m1_split).pack(side=tk.LEFT, padx=15)

        
        ttk.Label(r_ex, text="Y-Axis Scale:").pack(side=tk.LEFT, padx=(30, 5))
        self.m1_yscale = ttk.Combobox(r_ex, values=["Linear", "Log"], width=8); self.m1_yscale.set("Linear"); self.m1_yscale.pack(side=tk.LEFT)

        f_csv = ttk.Frame(f_ex); f_csv.pack(fill=tk.X, pady=5, padx=5)
        self.m1_pmode = tk.StringVar(value="base")
        def upd_m1_p(): self.m1_cpath.config(state='normal' if self.m1_pmode.get()=='custom' else 'disabled')
        ttk.Radiobutton(f_csv, text="Save to Base Path", variable=self.m1_pmode, value="base", command=upd_m1_p).pack(side=tk.LEFT)
        ttk.Radiobutton(f_csv, text="Custom Path:", variable=self.m1_pmode, value="custom", command=upd_m1_p).pack(side=tk.LEFT, padx=(10,0))
        self.m1_cpath = PlaceholderEntry(f_csv, width=25, placeholder="/path/", state='disabled'); self.m1_cpath.pack(side=tk.LEFT, padx=5)
        ttk.Label(f_csv, text="Filename:").pack(side=tk.LEFT, padx=(10, 0))
        self.m1_cname = PlaceholderEntry(f_csv, width=15, placeholder="output"); self.m1_cname.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.update_m1_dyn()

    def update_m1_dyn(self, e=None):
        for w in self.m1_dyn_frame.winfo_children(): w.destroy()
        ortho = get_ortho_axes(self.m1_cp_axis.get())
        if self.m1_type.get() == 'l':
            ttk.Label(self.m1_dyn_frame, text=f"Start ({ortho}):").pack(side=tk.LEFT)
            self.m1_p1 = PlaceholderEntry(self.m1_dyn_frame, width=8, placeholder="x y"); self.m1_p1.pack(side=tk.LEFT, padx=2)
            ttk.Label(self.m1_dyn_frame, text=f"Corner:").pack(side=tk.LEFT, padx=(5,0))
            self.m1_p2 = PlaceholderEntry(self.m1_dyn_frame, width=8, placeholder="x y"); self.m1_p2.pack(side=tk.LEFT, padx=2)
            ttk.Label(self.m1_dyn_frame, text=f"End:").pack(side=tk.LEFT, padx=(5,0))
            self.m1_p3 = PlaceholderEntry(self.m1_dyn_frame, width=8, placeholder="x y"); self.m1_p3.pack(side=tk.LEFT, padx=2)
        else:
            ttk.Label(self.m1_dyn_frame, text="Cutline Axis:").pack(side=tk.LEFT)
            self.m1_cl_ax = ttk.Combobox(self.m1_dyn_frame, values=["X","Y","Z"], width=5); self.m1_cl_ax.pack(side=tk.LEFT, padx=5)
            ttk.Label(self.m1_dyn_frame, text="Position:").pack(side=tk.LEFT, padx=(10, 0))
            self.m1_cl_pos = PlaceholderEntry(self.m1_dyn_frame, placeholder="e.g. 0.5"); self.m1_cl_pos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def add_m1_set(self):
        params = self.m1_params_frame.get_checked_items() or ["DopingConcentration"]
        data = {'cp_axis': self.m1_cp_axis.get(), 'cp_pos': self.m1_cp_pos.get_valid(), 'type': self.m1_type.get(), 'params': params}
        if data['type'] == 'l':
            data['points'] = f"\"{self.m1_p1.get_valid()}\" \"{self.m1_p2.get_valid()}\" \"{self.m1_p3.get_valid()}\""
            data['x_axis'] = 'Distance'
            display = f"Plane {data['cp_axis']}@{data['cp_pos']} -> L-Cut"
        else:
            data['cl_axis'] = self.m1_cl_ax.get()
            data['positions'] = [self.m1_cl_pos.get_valid().strip()]
            data['x_axis'] = get_axis_mapping(data['cp_axis'], data['cl_axis'])
            display = f"Plane {data['cp_axis']}@{data['cp_pos']} -> Line {data['cl_axis']}={data['positions'][0]}"
        self.m1_sets.append(data)
        self.m1_tree.insert("", "end", values=(data['type'].upper(), display, get_short_param_string(params)))

    def gen_m1(self):
        bp = self.glob_path.get_valid().strip()
        if bp and not bp.endswith('/'): bp += '/'
        csv_full = (bp if self.m1_pmode.get() == "base" else self.m1_cpath.get_valid()) + self.m1_cname.get_valid()
        self.generate_script(1, self.m1_sets, self.m1_same.get(), self.m1_yscale.get()=="Log",
                     csv_full, self.m1_split.get(), self.m1_enable_export.get())


    # ──────────────────────────────────────────────
    # Mode 2: 2D Analysis
    # ──────────────────────────────────────────────
    def init_mode2(self):
        self.tab2 = ttk.Frame(self.nb)
        self.nb.add(self.tab2, text="Mode 2: 2D Analysis")
        
        self.m2_canvas = tk.Canvas(self.tab2)
        sb = ttk.Scrollbar(self.tab2, orient="vertical", command=self.m2_canvas.yview)
        sf = ttk.Frame(self.m2_canvas)
        sf.bind("<Configure>", lambda e: self.m2_canvas.configure(scrollregion=self.m2_canvas.bbox("all")))
        self.m2_canvas.create_window((0,0), window=sf, anchor="nw")
        self.m2_canvas.bind('<Configure>', lambda e: self.m2_canvas.itemconfig(self.m2_canvas.create_window((0,0), window=sf, anchor="nw"), width=e.width))
        self.m2_canvas.configure(yscrollcommand=sb.set)
        self.m2_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        f_cut = ttk.LabelFrame(sf, text="Cut Set Configuration")
        f_cut.pack(fill=tk.X, padx=10, pady=5)
        
        r1 = ttk.Frame(f_cut); r1.pack(fill=tk.X, pady=5)
        ttk.Label(r1, text="Cut Type:").pack(side=tk.LEFT)
        self.m2_type = ttk.Combobox(r1, values=["full", "l"], width=5); self.m2_type.set("full"); self.m2_type.pack(side=tk.LEFT, padx=(5, 20))
        self.m2_type.bind("<<ComboboxSelected>>", self.update_m2_dyn)
        self.m2_dyn_frame = ttk.Frame(r1); self.m2_dyn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(f_cut, text="Select Parameters:").pack(anchor='w', padx=5, pady=(10,0))
        self.m2_params_frame = SimpleCheckBoxFrame(f_cut, PARAM_OPTIONS, columns=3)
        self.m2_params_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(f_cut, text="ADD CUT SET", command=self.add_m2_set).pack(fill=tk.X, padx=50, pady=10)

        # TABLE CONTAINER M2
        f_table_container = ttk.Frame(sf)
        f_table_container.pack(fill=tk.X, padx=10, pady=5)
        f_header = ttk.Frame(f_table_container); f_header.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(f_header, text="Active Cut Sets:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        def clear_m2_table():
            self.m2_sets.clear()
            for item in self.m2_tree.get_children(): self.m2_tree.delete(item)
        
        def delete_selected_m2():
            selected = self.m2_tree.selection()
            for item in reversed(selected):
                idx = self.m2_tree.index(item)
                del self.m2_sets[idx]
                self.m2_tree.delete(item)

        ttk.Button(f_header, text="Clear All", command=clear_m2_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_header, text="Delete Selected", command=delete_selected_m2).pack(side=tk.RIGHT, padx=2)

        f_tv = ttk.Frame(f_table_container); f_tv.pack(fill=tk.X, expand=True)
        m2_v = ttk.Scrollbar(f_tv, orient="vertical"); m2_h = ttk.Scrollbar(f_tv, orient="horizontal")
        self.m2_tree = ttk.Treeview(f_tv, columns=("Type", "Details", "Params"), show="headings", 
                                    height=3, yscrollcommand=m2_v.set, xscrollcommand=m2_h.set)
        m2_v.config(command=self.m2_tree.yview); m2_h.config(command=self.m2_tree.xview)
        self.m2_tree.heading("Type", text="Type"); self.m2_tree.heading("Details", text="Cut Details"); self.m2_tree.heading("Params", text="Parameters (Short)")
        self.m2_tree.column("Type", width=60, anchor="center"); self.m2_tree.column("Details", width=250, anchor="w"); self.m2_tree.column("Params", width=200, anchor="w")
        m2_v.pack(side=tk.RIGHT, fill=tk.Y); m2_h.pack(side=tk.BOTTOM, fill=tk.X); self.m2_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.m2_sets = []

        # Export M2
        f_ex = ttk.LabelFrame(sf, text="Export Options"); f_ex.pack(fill=tk.X, padx=10, pady=5)
        r_ex = ttk.Frame(f_ex)
        r_ex.pack(fill=tk.X, pady=2, padx=5)

        self.m2_enable_export = tk.BooleanVar(value=True)
        ttk.Checkbutton(r_ex, text="Enable CSV Export",
                        variable=self.m2_enable_export).pack(side=tk.LEFT, padx=(0,15))

        self.m2_same = tk.BooleanVar()
        ttk.Checkbutton(r_ex, text="Combine in Same Plot",
                        variable=self.m2_same).pack(side=tk.LEFT)

        self.m2_split = tk.BooleanVar()
        ttk.Checkbutton(r_ex, text="Split CSV by Cut Set",
                        variable=self.m2_split).pack(side=tk.LEFT, padx=15)

        # self.m2_same = tk.BooleanVar(); ttk.Checkbutton(r_ex, text="Combine in Same Plot", variable=self.m2_same).pack(side=tk.LEFT)
        # self.m2_split = tk.BooleanVar(); ttk.Checkbutton(r_ex, text="Split CSV by Cut Set", variable=self.m2_split).pack(side=tk.LEFT, padx=15)

        ttk.Label(r_ex, text="Y-Axis Scale:").pack(side=tk.LEFT, padx=(30, 5))
        self.m2_yscale = ttk.Combobox(r_ex, values=["Linear", "Log"], width=8); self.m2_yscale.set("Linear"); self.m2_yscale.pack(side=tk.LEFT)
        f_csv = ttk.Frame(f_ex); f_csv.pack(fill=tk.X, pady=5, padx=5)
        self.m2_pmode = tk.StringVar(value="base")
        def upd_m2_p(): self.m2_cpath.config(state='normal' if self.m2_pmode.get()=='custom' else 'disabled')
        ttk.Radiobutton(f_csv, text="Save to Base Path", variable=self.m2_pmode, value="base", command=upd_m2_p).pack(side=tk.LEFT)
        ttk.Radiobutton(f_csv, text="Custom Path:", variable=self.m2_pmode, value="custom", command=upd_m2_p).pack(side=tk.LEFT, padx=(10,0))
        self.m2_cpath = PlaceholderEntry(f_csv, width=25, placeholder="/path/", state='disabled'); self.m2_cpath.pack(side=tk.LEFT, padx=5)
        ttk.Label(f_csv, text="Filename:").pack(side=tk.LEFT, padx=(10, 0))
        self.m2_cname = PlaceholderEntry(f_csv, width=15, placeholder="output"); self.m2_cname.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.update_m2_dyn()

    def update_m2_dyn(self, e=None):
        for w in self.m2_dyn_frame.winfo_children(): w.destroy()
        if self.m2_type.get() == 'l':
            ttk.Label(self.m2_dyn_frame, text="Start:").pack(side=tk.LEFT)
            self.m2_p1 = PlaceholderEntry(self.m2_dyn_frame, width=8, placeholder="x y"); self.m2_p1.pack(side=tk.LEFT)
            ttk.Label(self.m2_dyn_frame, text="Corner:").pack(side=tk.LEFT, padx=5)
            self.m2_p2 = PlaceholderEntry(self.m2_dyn_frame, width=8, placeholder="x y"); self.m2_p2.pack(side=tk.LEFT)
            ttk.Label(self.m2_dyn_frame, text="End:").pack(side=tk.LEFT, padx=5)
            self.m2_p3 = PlaceholderEntry(self.m2_dyn_frame, width=8, placeholder="x y"); self.m2_p3.pack(side=tk.LEFT)
        else:
            ttk.Label(self.m2_dyn_frame, text="Axis (x/y):").pack(side=tk.LEFT)
            self.m2_ax = PlaceholderEntry(self.m2_dyn_frame, width=5, placeholder="X"); self.m2_ax.pack(side=tk.LEFT, padx=5)
            ttk.Label(self.m2_dyn_frame, text="Position:").pack(side=tk.LEFT, padx=10)
            self.m2_pos = PlaceholderEntry(self.m2_dyn_frame, placeholder="e.g. 0.5"); self.m2_pos.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def add_m2_set(self):
        params = self.m2_params_frame.get_checked_items() or ["DopingConcentration"]
        short_params_str = get_short_param_string(params)
        d = {'type': self.m2_type.get(), 'params': params}
        if d['type'] == 'l':
            d['points'] = f"\"{self.m2_p1.get_valid()}\" \"{self.m2_p2.get_valid()}\" \"{self.m2_p3.get_valid()}\""
            d['x_axis'] = 'Distance'
            detail = f"L-Cut ({d['points']})"
        else:
            d['axis'] = self.m2_ax.get_valid()
            d['positions'] = [self.m2_pos.get_valid().strip()]
            d['x_axis'] = 'X' if d['axis'].lower() == 'y' else 'Y'
            detail = f"Cut {d['axis']}={d['positions'][0]}"
        self.m2_sets.append(d)
        self.m2_tree.insert("", "end", values=(d['type'].upper(), detail, short_params_str))

    def gen_m2(self):
        bp = self.glob_path.get_valid().strip()
        if bp and not bp.endswith('/'): bp += '/'
        csv_full = (bp if self.m2_pmode.get() == "base" else self.m2_cpath.get_valid()) + self.m2_cname.get_valid()
        self.generate_script(2, self.m2_sets, self.m2_same.get(), self.m2_yscale.get()=="Log",
                     csv_full, self.m2_split.get(), self.m2_enable_export.get())


    # ──────────────────────────────────────────────
    # Mode 3: PLT Analysis
    # ──────────────────────────────────────────────
    def init_mode3(self):
        self.tab3 = ttk.Frame(self.nb)
        self.nb.add(self.tab3, text="Mode 3: PLT Analysis")
        
        # Canvas
        m3_canvas = tk.Canvas(self.tab3)
        sb = ttk.Scrollbar(self.tab3, orient="vertical", command=m3_canvas.yview)
        sf = ttk.Frame(m3_canvas)
        sf.bind("<Configure>", lambda e: m3_canvas.configure(scrollregion=m3_canvas.bbox("all")))
        m3_canvas.create_window((0,0), window=sf, anchor="nw")
        m3_canvas.bind('<Configure>', lambda e: m3_canvas.itemconfig(m3_canvas.create_window((0,0), window=sf, anchor="nw"), width=e.width))
        m3_canvas.configure(yscrollcommand=sb.set)
        m3_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # 1. File Configuration
        f_file = ttk.LabelFrame(sf, text="File Configuration"); f_file.pack(fill=tk.X, padx=10, pady=5)
        
        r1 = ttk.Frame(f_file); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="Base Path:", width=10).pack(side=tk.LEFT)
        self.m3_path = PlaceholderEntry(r1, placeholder="/home/sentaurus/projects/..."); self.m3_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        r2 = ttk.Frame(f_file); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text="PLT Prefix:", width=10).pack(side=tk.LEFT)
        self.m3_prefix = PlaceholderEntry(r2, placeholder="e.g. DeMOS"); self.m3_prefix.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. Node Manager
        f_nodes = ttk.LabelFrame(sf, text="Nodes Manager"); f_nodes.pack(fill=tk.X, padx=10, pady=5)
        
        r_add = ttk.Frame(f_nodes); r_add.pack(fill=tk.X, pady=2)
        ttk.Label(r_add, text="Version:").pack(side=tk.LEFT)
        self.m3_ver = PlaceholderEntry(r_add, width=10, placeholder="e.g. 4.5"); self.m3_ver.pack(side=tk.LEFT, padx=5)
        ttk.Label(r_add, text="Node ID:").pack(side=tk.LEFT)
        self.m3_nid = PlaceholderEntry(r_add, width=15, placeholder="e.g. n1250"); self.m3_nid.pack(side=tk.LEFT, padx=5)
        ttk.Button(r_add, text="Add Node", command=self.add_m3_node).pack(side=tk.LEFT, padx=20)

        # Nodes Table
        f_ntv = ttk.Frame(f_nodes); f_ntv.pack(fill=tk.X, pady=5)
        self.m3_tree = ttk.Treeview(f_ntv, columns=("Ver", "ID"), show="headings", height=4)
        self.m3_tree.heading("Ver", text="Version"); self.m3_tree.heading("ID", text="Node ID")
        self.m3_tree.column("Ver", width=100, anchor="center"); self.m3_tree.column("ID", width=150, anchor="w")
        self.m3_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Table Controls
        f_nctrl = ttk.Frame(f_nodes); f_nctrl.pack(fill=tk.X, pady=2)
        self.m3_nodes = []
        def del_m3_row():
            sel = self.m3_tree.selection()
            for s in reversed(sel): del self.m3_nodes[self.m3_tree.index(s)]; self.m3_tree.delete(s)
        def clear_m3(): self.m3_nodes.clear(); [self.m3_tree.delete(i) for i in self.m3_tree.get_children()]
        
        ttk.Button(f_nctrl, text="Clear List", command=clear_m3).pack(side=tk.RIGHT, padx=5)
        ttk.Button(f_nctrl, text="Delete Selected", command=del_m3_row).pack(side=tk.RIGHT, padx=5)

        # 3. Styling
        f_style = ttk.LabelFrame(sf, text="Plot Styling"); f_style.pack(fill=tk.X, padx=10, pady=5)
        
        r_s1 = ttk.Frame(f_style); r_s1.pack(fill=tk.X, pady=2)
        ttk.Label(r_s1, text="Plot Title:").pack(side=tk.LEFT)
        self.m3_title = PlaceholderEntry(r_s1, placeholder="My Plot Title"); self.m3_title.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        r_s2 = ttk.Frame(f_style); r_s2.pack(fill=tk.X, pady=2)
        ttk.Label(r_s2, text="X-Axis Title:").pack(side=tk.LEFT)
        self.m3_xtitle = PlaceholderEntry(r_s2, width=20, placeholder="Time (s)"); self.m3_xtitle.pack(side=tk.LEFT, padx=5)
        ttk.Label(r_s2, text="Y-Axis Title:").pack(side=tk.LEFT, padx=5)
        self.m3_ytitle = PlaceholderEntry(r_s2, width=20, placeholder="Voltage (V)"); self.m3_ytitle.pack(side=tk.LEFT, padx=5)
        ttk.Label(r_s2, text="Y2-Axis Title:").pack(side=tk.LEFT, padx=5)
        self.m3_y2title = PlaceholderEntry(r_s2, width=20, placeholder="Temperature (K)"); self.m3_y2title.pack(side=tk.LEFT, padx=5)

        r_s3 = ttk.Frame(f_style); r_s3.pack(fill=tk.X, pady=2)
        ttk.Label(r_s3, text="Legend Pos (X Y):").pack(side=tk.LEFT)
        self.m3_lx = PlaceholderEntry(r_s3, width=10, placeholder="0.8"); self.m3_lx.pack(side=tk.LEFT, padx=2)
        self.m3_ly = PlaceholderEntry(r_s3, width=10, placeholder="0.9"); self.m3_ly.pack(side=tk.LEFT, padx=2)

        # 4. Export
        f_ex = ttk.LabelFrame(sf, text="Export"); f_ex.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(f_ex, text="CSV Filename:").pack(side=tk.LEFT)
        self.m3_csv = PlaceholderEntry(f_ex, width=20, placeholder="output"); self.m3_csv.pack(side=tk.LEFT, padx=10)
        ttk.Label(f_ex, text="PNG Path:").pack(side=tk.LEFT)
        self.m3_png = PlaceholderEntry(f_ex, placeholder="/path/to/image.png"); self.m3_png.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

    def add_m3_node(self):
        v, n = self.m3_ver.get_valid(), self.m3_nid.get_valid()
        if v and n:
            self.m3_nodes.append((v, n))
            self.m3_tree.insert("", "end", values=(v, n))

    def gen_m3(self):
        if not self.m3_nodes: messagebox.showerror("Error", "No nodes added!"); return
        bp = self.m3_path.get_valid().strip()
        if bp and not bp.endswith('/'): bp += '/'
        prefix = self.m3_prefix.get_valid()
        
        cmds = []
        
        v1, n1 = self.m3_nodes[0]
        cmds += [f"load_file {bp}{prefix}_{v1}_{n1}_des.plt", "create_plot -1d", "select_plots {Plot_1}"]
        
        for v, n in self.m3_nodes[1:]: cmds.append(f"load_file {bp}{prefix}_{v}_{n}_des.plt")
        
        all_dsets = " ".join(f"{prefix}_{v}_{n}_des" for v, n in self.m3_nodes)
        
        cmds.append(f"create_curve -axisX time -axisY {{drain OuterVoltage}} -dataset {{{all_dsets}}} -plot Plot_1")
        cmds.append(f"create_curve -axisX time -axisY2 Tmax -dataset {{{all_dsets}}} -plot Plot_1")
        
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ff8000", "#800080", "#008080"]
        tmax_start = len(self.m3_nodes) + 1
        
        for i, (v, n) in enumerate(self.m3_nodes):
            curve_num = tmax_start + i
            color = colors[i % len(colors)]
            cmds.append(f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -line_style dash -line_width 2 -color {color} -hide_legend")
            cmds.append(f"set_curve_prop {{Curve_{i+1}}} -plot Plot_1 -line_width 2")
            cmds.append(f"set_curve_prop {{Curve_{i+1}}} -plot Plot_1 -label \"drain OuterVoltage_{v}\"")

        cmds.append(f"set_axis_prop -plot Plot_1 -axis y2 -title \"{self.m3_y2title.get_valid()}\"")
        cmds.append(f"set_axis_prop -plot Plot_1 -axis x -title \"{self.m3_xtitle.get_valid()}\"")
        cmds.append(f"set_axis_prop -plot Plot_1 -axis y -title \"{self.m3_ytitle.get_valid()}\"")
        cmds.append(f"set_plot_prop -plot {{Plot_1}} -title \"{self.m3_title.get_valid()}\" -frame_width 2")
        
        lx, ly = self.m3_lx.get_valid(), self.m3_ly.get_valid()
        if lx and ly: cmds.append(f"set_legend_prop -plot Plot_1 -position {{{lx} {ly}}}")
        
        cmds.append(f"move_plot -plot Plot_1 -position {{0 0}}")

        if self.m3_png.get_valid(): cmds.append(f"export_view {{{self.m3_png.get_valid()}}} -format png")
        
        csv = f"{bp}{self.m3_csv.get_valid()}.csv"
        all_c = " ".join(f"Curve_{i}" for i in range(1, len(self.m3_nodes)*2 + 1))
        cmds.append(f"export_curves {{{all_c}}} -plot Plot_1 -filename {csv} -format csv")

        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, "\n".join(cmds))

    # ──────────────────────────────────────────────
    # GENERATOR (Logic with Parameterized Filenames)
    # ──────────────────────────────────────────────
    def generate_script(self, mode, sets, same_plot, log_y, csv_path_full, split_sets, enable_export):

        try:
            nodes = [x.strip() for x in self.glob_nodes.get_valid().split(',') if x.strip()]
            tdrs = [f"00{x.strip()}" if len(x.strip())==2 else x.strip() for x in self.glob_tdrs.get_valid().split(',') if x.strip()]
            
            # Param Logic
            param_name = self.glob_pname.get_valid().strip()
            param_vals_str = self.glob_pvals.get_valid().strip()
            param_vals = [x.strip() for x in param_vals_str.split(',') if x.strip()]

            if param_name and len(param_vals) != len(nodes):
                messagebox.showerror("Error", f"Mismatch: {len(nodes)} Nodes vs {len(param_vals)} Parameter Values.")
                return

            bp = self.glob_path.get_valid().strip()
            if bp and not bp.endswith('/'): bp += '/'
            
            all_files = []
            
            for i, n in enumerate(nodes):
                param_str = ""
                if param_name:
                    param_str = f"_{param_name}{param_vals[i]}"
                
                for c in tdrs: 
                    all_files.append(f"{n}{param_str}_{c}")
                
                if self.last_tdr_var.get() == 'yes': 
                    all_files.append(n)

            if not all_files:
                messagebox.showerror("Error", "No valid Nodes/TDRs found.")
                return

            cmds = []
            
            for f in all_files:
                cmds.append(f"load_file {bp}{f}_des.tdr -fod")
                cmds.append(f"create_plot -dataset {f}_des")
            
            all_plots = " ".join(f"Plot_{f}_des" for f in all_files)
            cmds.extend([f"select_plots {{{all_plots}}}", f"link_plots {{{all_plots}}}"])

            export_registry = []
            plot_map = {}
            curve_cnt = 1
            y_type = "log" if log_y else "linear"

            for set_idx, s in enumerate(sets, start=1):
                for p in s['params']:
                    cmds.append(f"set_field_prop {p} -plot Plot_{all_files[-1]}_des -geom {all_files[-1]}_des -show_bands")

                for i, f in enumerate(all_files):
                    plot_root = f"Plot_{f}_des"
                    cmds.append(f"select_plots {{{plot_root}}}")
                    
                    if mode == 1:
                        cmds.append(f"create_cutplane -plot {plot_root} -type {s['cp_axis']} -at {s['cp_pos']}")
                        cp_dset = f"C{set_idx}({f}_des)"
                        plot_inter = f"Plot_{cp_dset}"
                        cmds.append(f"create_plot -dataset {cp_dset} -ref_plot {plot_root}")
                        cmds.append(f"select_plots {{{plot_inter}}}")
                    else:
                        plot_inter = plot_root

                    if s['type'] == 'l':
                        cmds.append(f"create_cutpolyline -plot {plot_inter} -points {{{s['points']}}}")
                    else:
                        pos = s['positions'][0]
                        if mode == 1:
                            cmds.append(f"create_cutline -plot {plot_inter} -type {s['cl_axis']} -at {pos}")
                        else:
                            cmds.append(f"create_cutline -plot {plot_inter} -type {s['axis']} -at {pos}")

                    final_dset = f"C1(C{set_idx}({f}_des))" if mode == 1 else f"C{set_idx}({f}_des)"

                    for p in s['params']:
                        short = ABBREVIATIONS.get(p, p)
                        key = 'Unified' if same_plot else p
                        tcl_var = f"{key.replace(' ','')}"
                        
                        if key not in plot_map:
                            cmds.append(f"create_plot -dataset {final_dset} -1d")
                            cmds.append(f"set {tcl_var} [lindex [list_plots] end]")
                            title = "Comparison" if same_plot else short
                            cmds.append(f"set_plot_prop -plot ${tcl_var} -title \"{title}\"")
                            cmds.append(f"set_axis_prop -plot ${tcl_var} -axis y -type {y_type}")
                            plot_map[key] = f"${tcl_var}"
                        
                        target = plot_map[key]
                        c_name = f"Curve_{curve_cnt}"
                        cmds.append(f"create_curve -axisX {s['x_axis']} -axisY {p} -dataset {{{final_dset}}} -plot {target}")
                        
                        export_registry.append({
                            'set': set_idx,
                            'param': short,
                            'plot': target,
                            'curve': c_name
                        })
                        curve_cnt += 1  

# -------------------- FIXED EXPORT: ONE CSV PER PARAMETER --------------------
# -------------------- EXPORT SECTION --------------------

            if not enable_export:
                self.txt_output.delete("1.0", tk.END)
                self.txt_output.insert(tk.END, "\n".join(cmds))
                return


            from collections import defaultdict

            # Group by (parameter, plot, cutset)
            param_groups = defaultdict(list)

            for entry in export_registry:
                key = (entry['param'], entry['plot'], entry['set'])
                param_groups[key].append(entry)


            processed = set()

            for (param, plot, cutset), entries in param_groups.items():

                # Build local curve list (Curve_1 ... Curve_N)
                num_curves = len(entries)
                curve_list = " ".join([f"Curve_{i+1}" for i in range(num_curves)])

                cmds.append(f"select_plots {plot}")

                # ----- FILE NAMING LOGIC -----

                if split_sets:
                    # Separate CSV for each cutset
                    fname = f"{csv_path_full}_{param}_Set{cutset}.csv"
                else:
                    # Single CSV per parameter
                    if param in processed:
                        continue

                    processed.add(param)
                    fname = f"{csv_path_full}_{param}.csv"

                cmds.append(
                    f"export_curves {{{curve_list}}} -plot {plot} -filename {fname} -format csv"
                )

            # ---------------------------------------------------------


            self.txt_output.delete("1.0", tk.END)
            self.txt_output.insert(tk.END, "\n".join(cmds))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_out(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.txt_output.get("1.0", tk.END))
    def save_out(self):
        f = filedialog.asksaveasfilename(defaultextension=".tcl")
        if f:
            with open(f, 'w') as file: file.write(self.txt_output.get("1.0", tk.END))

if __name__ == "__main__":
    root = tk.Tk()
    app = TCADGeneratorApp(root)
    root.mainloop()