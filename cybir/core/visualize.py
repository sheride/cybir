"""Interactive plotly visualization of the EKC phase graph.

Nodes are phases (colored by type: FRST/vex/non-inherited).
Edges are contractions (colored by contraction type).
Self-loops represent terminal walls (asymptotic, CFT, su(2), symmetric flop).
Hover over nodes/edges for detailed information.
"""

import numpy as np
import plotly.graph_objects as go


# --- Color schemes ---

_PHASE_COLORS = {
    "frst": "#2ecc71",         # green
    "vex": "#3498db",          # blue
    "non_inherited": "#e74c3c", # red
    None: "#95a5a6",           # gray (unknown / check_toric not run)
}

_CONTRACTION_COLORS = {
    "ASYMPTOTIC": "#7f8c8d",      # gray
    "CFT": "#9b59b6",             # purple
    "SU2": "#e67e22",             # orange
    "SU2_NONGENERIC_CS": "#d35400", # dark orange
    "SYMMETRIC_FLOP": "#2980b9",  # blue
    "GROSS_FLOP": "#c0392b",      # dark red
    "FLOP": "#27ae60",            # green
    "UNRESOLVED": "#bdc3c7",      # light gray
}

_CONTRACTION_DISPLAY = {
    "ASYMPTOTIC": "Asymptotic",
    "CFT": "CFT",
    "SU2": "SU(2)",
    "SU2_NONGENERIC_CS": "SU(2) tuned",
    "SYMMETRIC_FLOP": "Sym. flop",
    "GROSS_FLOP": "Gross flop",
    "FLOP": "Flop",
    "UNRESOLVED": "Unresolved",
}


def plot_phase_graph(ekc, width=900, height=700, title=None, fig=None):
    """Create an interactive plotly visualization of the EKC phase graph.

    Parameters
    ----------
    ekc : CYBirationalClass
        The EKC object (after from_gv, optionally after apply_coxeter_orbit).
    width : int, optional
        Figure width in pixels.
    height : int, optional
        Figure height in pixels.
    title : str, optional
        Figure title. Defaults to summary string.
    fig : go.FigureWidget, optional
        Existing figure to update (for animation). If None, creates new.

    Returns
    -------
    go.FigureWidget
        Interactive plotly figure.
    """
    graph = ekc._graph._graph
    phases = list(graph.nodes())
    n_phases = len(phases)

    if n_phases == 0:
        raise ValueError("No phases in graph")

    # --- Layout: planar if possible, then spring, then circular fallback ---
    pos = _best_layout(graph, phases)

    # --- Collect phase type info ---
    phase_types = getattr(ekc, '_phase_types', {})

    # --- Build edge traces (one per contraction type for legend grouping) ---
    # Separate cross-edges from self-loops
    edge_traces = {}  # type_name -> {x, y, text, color}
    loop_traces = {}  # type_name -> {x, y, text, color}

    for u, v, data in graph.edges(data=True):
        c = data["contraction"]
        ctype = c.contraction_type.name if c.contraction_type else "UNRESOLVED"
        color = _CONTRACTION_COLORS.get(ctype, "#bdc3c7")
        display = _CONTRACTION_DISPLAY.get(ctype, ctype)

        # Build hover text
        curve_str = str([int(x) for x in c.contraction_curve])
        hover_parts = [f"<b>{display}</b>", f"Curve: {curve_str}"]
        if c.zero_vol_divisor is not None:
            zvd_str = str([int(round(x)) for x in c.zero_vol_divisor])
            hover_parts.append(f"ZVD: {zvd_str}")
        if c.gv_invariant is not None:
            hover_parts.append(f"n₀ = {c.gv_invariant}")
        if c.gv_series is not None:
            hover_parts.append(f"GV series: {c.gv_series[:5]}")
        hover_parts.append(f"{u} — {v}")
        hover_text = "<br>".join(hover_parts)

        if u == v:
            # Self-loop
            bucket = loop_traces
        else:
            bucket = edge_traces

        if ctype not in bucket:
            bucket[ctype] = {"x": [], "y": [], "text": [],
                             "color": color, "display": display}

        if u == v:
            # Draw self-loop as a small arc
            _add_self_loop(bucket[ctype], pos[u], u, phases, pos)
            bucket[ctype]["text"].append(hover_text)
        else:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            # Midpoint for hover
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            bucket[ctype]["x"].extend([x0, x1, None])
            bucket[ctype]["y"].extend([y0, y1, None])
            bucket[ctype]["text"].append(hover_text)

    data_traces = []

    # Edge lines (cross-edges)
    for ctype, edata in edge_traces.items():
        line_trace = go.Scatter(
            x=edata["x"], y=edata["y"],
            mode="lines",
            line=dict(color=edata["color"], width=2.5),
            hoverinfo="skip",
            showlegend=True,
            name=edata["display"],
            legendgroup=ctype,
        )
        data_traces.append(line_trace)

        # Invisible midpoint markers for hover
        mid_x, mid_y, mid_text = [], [], []
        xs, ys = edata["x"], edata["y"]
        text_idx = 0
        i = 0
        while i < len(xs) - 2:
            if xs[i] is not None and xs[i+1] is not None:
                mid_x.append((xs[i] + xs[i+1]) / 2)
                mid_y.append((ys[i] + ys[i+1]) / 2)
                if text_idx < len(edata["text"]):
                    mid_text.append(edata["text"][text_idx])
                text_idx += 1
            i += 3  # skip the None separator

        hover_trace = go.Scatter(
            x=mid_x, y=mid_y,
            mode="markers",
            marker=dict(size=12, color=edata["color"], opacity=0),
            text=mid_text,
            hoverinfo="text",
            showlegend=False,
            legendgroup=ctype,
        )
        data_traces.append(hover_trace)

    # Self-loop traces
    for ctype, ldata in loop_traces.items():
        loop_line = go.Scatter(
            x=ldata["x"], y=ldata["y"],
            mode="lines",
            line=dict(color=ldata["color"], width=2, dash="dot"),
            hoverinfo="skip",
            showlegend=ctype not in edge_traces,
            name=ldata["display"] + " (terminal)" if ctype not in edge_traces else None,
            legendgroup=ctype,
        )
        data_traces.append(loop_line)

        # Hover markers at loop apex
        loop_hover_x, loop_hover_y = [], []
        # Extract apex points (every loop is drawn with ~20 points + None)
        xs, ys = ldata["x"], ldata["y"]
        text_idx = 0
        loop_texts = []
        i = 0
        segment_points = []
        for j, x in enumerate(xs):
            if x is None:
                if segment_points:
                    # Apex is roughly the midpoint of the arc
                    mid = len(segment_points) // 2
                    px, py = segment_points[mid]
                    loop_hover_x.append(px)
                    loop_hover_y.append(py)
                    if text_idx < len(ldata["text"]):
                        loop_texts.append(ldata["text"][text_idx])
                    text_idx += 1
                    segment_points = []
            else:
                segment_points.append((x, ys[j]))

        if loop_hover_x:
            loop_hover = go.Scatter(
                x=loop_hover_x, y=loop_hover_y,
                mode="markers",
                marker=dict(size=10, color=ldata["color"], opacity=0),
                text=loop_texts,
                hoverinfo="text",
                showlegend=False,
                legendgroup=ctype,
            )
            data_traces.append(loop_hover)

    # --- Node trace ---
    node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
    for label in phases:
        x, y = pos[label]
        node_x.append(x)
        node_y.append(y)

        phase = graph.nodes[label]["phase"]
        ptype = phase_types.get(label)
        node_colors.append(_PHASE_COLORS.get(ptype, _PHASE_COLORS[None]))

        # Hover text
        hover_parts = [f"<b>{label}</b>"]
        if ptype:
            hover_parts.append(f"Type: {ptype}")
        hover_parts.append(f"c₂ = {[int(x) for x in phase.c2]}")
        kappa = phase.int_nums
        hover_parts.append(f"κ sum = {int(kappa.sum())}")
        if phase.kahler_cone is not None:
            n_rays = len(list(phase.kahler_cone.rays()))
            hover_parts.append(f"Kähler rays: {n_rays}")
        if phase.tip is not None:
            tip_str = str([round(float(x), 3) for x in phase.tip])
            hover_parts.append(f"Tip: {tip_str}")

        # Count edges by type
        edge_summary = {}
        for _, _, edata in graph.edges(label, data=True):
            ct = edata["contraction"].contraction_type
            name = ct.name if ct else "UNRESOLVED"
            dname = _CONTRACTION_DISPLAY.get(name, name)
            edge_summary[dname] = edge_summary.get(dname, 0) + 1
        if edge_summary:
            hover_parts.append("Walls: " + ", ".join(
                f"{v}× {k}" if v > 1 else k
                for k, v in sorted(edge_summary.items())
            ))

        node_text.append("<br>".join(hover_parts))
        node_sizes.append(25)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="white"),
        ),
        text=[l for l in phases],
        textposition="top center",
        textfont=dict(size=11, color="black"),
        hovertext=node_text,
        hoverinfo="text",
        showlegend=False,
        name="Phases",
    )
    data_traces.append(node_trace)

    # --- Title ---
    if title is None:
        parts = [f"{n_phases} phases"]
        coxeter_order = ekc.coxeter_order
        if coxeter_order is not None and coxeter_order > 1:
            parts.append(f"|W| = {coxeter_order}")
        elif coxeter_order is None:
            parts.append("infinite Coxeter")
        n_flops = sum(1 for c in ekc.contractions
                      if c.contraction_type and c.contraction_type.name == "FLOP")
        n_terminal = sum(1 for c in ekc.contractions
                         if c.contraction_type and c.contraction_type.name
                         in ("ASYMPTOTIC", "CFT", "SU2", "SU2_NONGENERIC_CS",
                             "SYMMETRIC_FLOP"))
        parts.append(f"{n_flops} flops, {n_terminal} terminal")
        title = "EKC Phase Graph — " + ", ".join(parts)

    # --- Assemble figure ---
    if fig is None:
        fig = go.FigureWidget(data=data_traces)
    else:
        with fig.batch_update():
            old_data = len(fig.data)
            fig.add_traces(data_traces)
            fig.data = fig.data[old_data:]

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        width=width,
        height=height,
        showlegend=True,
        legend=dict(
            x=1.02, y=1, bordercolor="black", borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x"),
        plot_bgcolor="white",
        margin=dict(l=20, r=150, t=60, b=20),
        hovermode="closest",
    )

    return fig


# --- Layout helpers ---

def _best_layout(graph, phases):
    """Choose the best layout to avoid edge crossings.

    Priority: planar (no crossings guaranteed) > Kamada-Kawai (good for
    small graphs) > spring (fallback).
    """
    import networkx as nx

    # Build a simple graph (no self-loops, no multi-edges) for layout
    simple = nx.Graph(graph)
    simple.remove_edges_from(nx.selfloop_edges(simple))

    # Try planar layout first
    is_planar, _ = nx.check_planarity(simple)
    if is_planar and len(phases) > 1:
        try:
            pos = nx.planar_layout(simple)
            return pos
        except Exception:
            pass

    # Kamada-Kawai for small/medium graphs (minimizes edge length variance)
    if len(phases) <= 20:
        try:
            pos = nx.kamada_kawai_layout(simple)
            return pos
        except Exception:
            pass

    # Spring layout fallback with high iteration count
    pos = nx.spring_layout(simple, iterations=200, seed=42, k=2.0 / max(1, len(phases) ** 0.5))
    return pos


def _add_self_loop(bucket, center, label, phases, pos, radius=0.12, n_pts=20):
    """Draw a self-loop as a small arc outside the node."""
    cx, cy = center

    # Find angle away from other nodes
    angles_to_neighbors = []
    for other in phases:
        if other == label:
            continue
        ox, oy = pos[other]
        angles_to_neighbors.append(np.arctan2(oy - cy, ox - cx))

    if angles_to_neighbors:
        # Point loop away from the center of mass of neighbors
        avg_angle = np.mean(angles_to_neighbors)
        loop_angle = avg_angle + np.pi  # opposite direction
    else:
        loop_angle = np.pi / 2  # default: upward

    # Draw arc
    arc_center_x = cx + radius * np.cos(loop_angle)
    arc_center_y = cy + radius * np.sin(loop_angle)

    theta = np.linspace(0, 2 * np.pi, n_pts)
    r = radius * 0.5
    loop_x = list(arc_center_x + r * np.cos(theta))
    loop_y = list(arc_center_y + r * np.sin(theta))
    loop_x.append(None)
    loop_y.append(None)

    bucket["x"].extend(loop_x)
    bucket["y"].extend(loop_y)
