# -*- coding: utf-8 -*-
"""
Created on Sun Jun 29 11:02:12 2025

@author: Lequan Wang and Haibei Li
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go


def homepage():
    st.set_page_config(
       page_title="Visualizing Potential Well",
       layout="centered",
      page_icon=":bar_chart:"
    )

    st.markdown(
    """
    <h1 style="text-align:center; font-size:2.7rem; margin-top:2.5rem; margin-bottom:2.5rem;">
    <span style="color:red;">Visualizing</span> n-Dimensional Infinite Potential Well
    </h1>
    """,
    unsafe_allow_html=True
    )
    st.markdown(
    """
    <h2 style="text-align:center; font-size:1.5rem; margin-top:0rem; margin-bottom:2.5rem;">
    <span style="color:dimgray;">By Lequan Wang and Haibei Li </span>
    </h2>
    """,
    unsafe_allow_html=True
    )
    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("1-Dimension", width="stretch", on_click=goto_page, args=("1D",))
    with c2:
        st.button("2-Dimension", width="stretch", on_click=goto_page, args=("2D",))
    with c3:
        st.button("3-Dimension", width="stretch", on_click=goto_page, args=("3D",))

@st.cache_data(ttl=3600)
def _calculate_static_data_1d():
    _n_arr = np.arange(1, 8)[:, np.newaxis] # 列向量
    _L_arr = np.linspace(1,5,201)
    _energy_all = _n_arr ** 2 * np.pi ** 2 / (2 * _L_arr ** 2)
    return _energy_all, _n_arr, _L_arr

def display_1d_infinite_well():
    # 缓存数据
    energy_all, n_arr, L_arr = _calculate_static_data_1d()

    # 标题和页面设置
    st.set_page_config(
        page_title="1D Infinite Well",
        layout="wide",
    )
    st.title(':red[1D] Infinite Square Well')

    # 侧边栏
    with st.sidebar:
        st.header('Formulas')
        st.latex(r'\Psi_n(x) = \sqrt{\frac{2}{L}} \sin\left(\frac{n\pi x}{L}\right)')
        st.latex(r'E_n = \frac{n^2\pi^2 \hbar^2}{2m_eL^2}')
        st.header('Set parameters')
        n = st.slider('Quantum Number $(n)$',
                      min_value=1, max_value=n_arr[-1,0],
                      value=1, step=1)
        L = st.slider('Length $(L)$',
                      min_value=L_arr[0], max_value=L_arr[-1],
                      value=L_arr[0], step=0.02)
        save_image = st.button(label='Save Image', help="save image as SVG")
        st.button(label="←--- back to home", on_click=goto_page, args=("Home",))

    # 波函数方程
    def psi(x, n, l):
        return np.sqrt(2 / l) * np.sin(n * np.pi * x / l)

    # 能量方程
    def energy(n, l):
        return n ** 2 * np.pi ** 2 / (2 * l ** 2)

    # 波函数数据
    x_arr = np.linspace(0, L, 200)
    psi_arr = psi(x_arr, n_arr, L)
    psi2_arr = psi_arr ** 2

    # 能量数据
    energy_arr = energy(n_arr, L)
    energy_point = energy_arr[n-1]

    # 波函数+能量数据
    psi_energy = psi_arr * 5 / L ** 2 + energy_arr

    # 颜色定义
    colors=['#311b92','#283593','#1976d2','#039be5','#00bcd4','#26a69a','#81c784']

    # 创建图框架
    fig = plt.figure(figsize=(12,7), layout='tight')
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1],)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[:, 1])

    # 单个波函数图（图1）
    ax1.plot(x_arr, psi_arr[n-1],
             label=rf'$\Psi_{n}(x)$', color=colors[n-1])
    ax1.plot(x_arr, psi2_arr[n-1],
             label=rf'$\Psi_{n}^2(x)$', color='red')
    ax1.set(xlabel='$x$', xlim=(0, L),
            ylabel=(r'$\Psi \quad \text{and} \quad \Psi^2$'), ylim=(-2.5, 2.5),
            title='Wavefunction and Probability Density')
    ax1.fill_between(x_arr,  psi2_arr[n-1], alpha=0.2, color='red')
    ax1.legend(loc='lower left')

    # 多个能量图（图2）
    for i in range(len(n_arr)-1,-1,-1):
        ax2.plot(L_arr, energy_all[i], label=f'$E_{i+1}$',
                 color=colors[i], zorder=i)
    ax2.scatter(L, energy_point, color='red', marker='.', zorder=10)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.75, zorder=-10)
    ax2.vlines(L, ymin=0, ymax=energy_point, color='red',
               linestyle='--', linewidth=0.75, zorder=9)
    ax2.hlines(energy_point, xmin=0, xmax=L, color='red',
               linestyle='--', linewidth=0.75, zorder=9)
    ax2.set(xlabel='$L$', xlim=(1,5),
            ylabel=r'$E_n \quad (a.u.)$', ylim=(-5, 130),
            title='Energy Levels')
    ax2.legend(loc='upper right')

    # 多个波函数图（图3）
    yticks_ax3 = psi_energy[:,0]
    yticklabels_ax3 = [f'{tick:.1f}' for tick in yticks_ax3]
    for i in range(len(n_arr)-1,-1,-1):
        ax3.plot(x_arr, psi_energy[i], label=rf'$\psi_{i+1}$',
                 color=colors[i], zorder=i)
        ax3.axhline(y=yticks_ax3[i], color='gray', linestyle='-', linewidth=0.75, zorder=-10)
    ax3.set(xlabel='$x$', xlim=(0, L),
            ylabel=r'$E_n \quad (a.u.)$', ylim=(0, 250/L ** 2),
            yticks=yticks_ax3,yticklabels=yticklabels_ax3,
            title='Wavefunctions with Energy Levels')
    st.pyplot(fig)
    if save_image:
        plt.savefig("1D Infinite Square Well.svg", format='svg')
        st.balloons()

def display_2d_infinite_well():

    # 标题和页面设置
    st.set_page_config(
        page_title="2D Infinite Well",
        layout="wide",
    )
    st.title(':red[2D] Infinite Square Well')

    # 侧边栏
    with st.sidebar:
        st.header('Formulas')
        st.latex(
            r"""\Psi_{n_x,n_y}(x, y) = \sqrt{\frac{4}{L_x L_y}} \sin\left(\frac{n_x\pi x}{L_x}\right)\sin\left(\frac{n_y\pi y}{L_y}\right)""")
        st.latex(r"""E_{n_x,n_y} = \frac{\pi^2\hbar^2}{2m_e}\left(\frac{n_x^2}{L_x^2} + \frac{n_y^2}{L_y^2}\right)""")
        st.header('Set parameters')
        n_max = 5
        n_x = st.slider('Quantum number $x$ $(n_{x})$', min_value=1, max_value=n_max, value=1, step=1)
        n_y = st.slider('Quantum number $y$ $(n_{y})$', min_value=1, max_value=n_max, value=1, step=1)
        L_x = st.slider('Length $x$ $(L_{x})$', min_value=1.0, max_value=5.0, value=1.0, step=0.1)
        L_y = st.slider('Length $y$ $(L_{y})$', min_value=1.0, max_value=5.0, value=1.0, step=0.1)
        st.button(label="←—— back to home", on_click=goto_page, args=("Home",))

    # 波函数公式
    def psi_2d(x, y, n_x, n_y, L_x, L_y):
        return np.sqrt(4 / (L_x * L_y)) * np.sin(n_x * np.pi * x / L_x) * np.sin(n_y * np.pi * y / L_y)

    # 波函数数据
    num_points = 80
    x = np.linspace(0, L_x, num_points)
    y = np.linspace(0, L_y, num_points)
    X, Y = np.meshgrid(x, y)
    psi = psi_2d(X, Y, n_x, n_y, L_x, L_y)
    psi2 = psi ** 2

    # 波函数3D
    fig_psi3d = go.Figure(data=[
        go.Surface(z=psi, x=x, y=y,
                   colorscale='RdBu', colorbar=dict(title='Amplitude'),
                   showscale=True)
        ])
    fig_psi3d.update_layout(
        title={'text': 'Wavefunction (Ψ)', 'x': 0.45, 'xanchor': 'center'},
        title_font=dict(size=22),
        scene=dict(
            xaxis_title='x', yaxis_title='y', zaxis_title='Ψ',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        height=800,
    )

    # 概率密度3D
    fig_psi2_3d = go.Figure(data=[
        go.Surface(
            z=psi2, x=x, y=y, colorscale='viridis', colorbar=dict(title='Pro. Density'), showscale=True
        )])
    fig_psi2_3d.update_layout(
        title={'text': 'Probability Density (Ψ²)', 'x': 0.45, 'xanchor': 'center'},
        title_font=dict(size=22),
        scene=dict(
            xaxis_title='x', yaxis_title='y', zaxis_title='Ψ²',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        height=800,
    )

    # 2*2绘图
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_psi3d)
        #st.plotly_chart(fig_psi_contour)
    with c2:
        st.plotly_chart(fig_psi2_3d)
        #st.plotly_chart(fig_psi2_contour)

    # -- 数据
    ns = np.arange(1, n_max + 1)
    nx, ny = np.meshgrid(ns, ns)
    nx_vals = nx.flatten()
    ny_vals = ny.flatten()
    En_vals = (np.pi ** 2 / 2) * ((nx_vals ** 2) / (L_x ** 2) + (ny_vals ** 2) / (L_y ** 2))

    dx = 0.9
    dy = 0.9

    def cuboid_data(center, size, height):
        x, y = center
        dx2, dy2 = size[0] / 2, size[1] / 2
        pts = np.array([
            [x - dx2, y - dy2, 0],
            [x + dx2, y - dy2, 0],
            [x + dx2, y + dy2, 0],
            [x - dx2, y + dy2, 0],
            [x - dx2, y - dy2, height],
            [x + dx2, y - dy2, height],
            [x + dx2, y + dy2, height],
            [x - dx2, y + dy2, height],
        ])
        return pts

    def cuboid_edges(pts):
        """返回立方体12条边，每条用首末点索引，结果适配 Plotly Scatter3d"""
        edge_index = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
            [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
            [0, 4], [1, 5], [2, 6], [3, 7]  # 立柱
        ]
        lines_x, lines_y, lines_z = [], [], []
        for (i, j) in edge_index:
            lines_x += [pts[i][0], pts[j][0], None]
            lines_y += [pts[i][1], pts[j][1], None]
            lines_z += [pts[i][2], pts[j][2], None]
        return lines_x, lines_y, lines_z

    fig = go.Figure()

    for ix, iy, energy in zip(nx_vals, ny_vals, En_vals):
        color = 'firebrick' if (ix == n_x and iy == n_y) else 'cornflowerblue'
        opacity = 1
        pts = cuboid_data((ix, iy), (dx, dy), energy)

        # 柱体本体
        faces = [
            [0, 1, 2], [0, 2, 3],
            [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4],
            [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6],
            [3, 0, 4], [3, 4, 7]
        ]
        I, J, K = zip(*faces)
        fig.add_trace(go.Mesh3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            i=I, j=J, k=K,
            color=color,
            opacity=opacity,
            flatshading=True,
            hovertext=f"nₓ={ix}<br>nᵧ={iy}<br>E={energy:.2f}",
            hoverinfo="text",
            showscale=False
        ))

        # 柱体12条边线
        edge_color = 'black'
        lines_x, lines_y, lines_z = cuboid_edges(pts)
        fig.add_trace(go.Scatter3d(
            x=lines_x, y=lines_y, z=lines_z,
            mode='lines',
            line=dict(color=edge_color, width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

    fig.update_layout(
        title={'text': 'Energy Levels', 'x': 0.5, 'xanchor': 'center'},
        title_font=dict(size=22),
        scene=dict(
            xaxis_title="nₓ",
            yaxis_title="nᵧ",
            zaxis_title="Energy (a.u.)",
            xaxis=dict(
                tickvals=list(range(1, n_max + 1)),
                ticktext=[str(i) for i in range(1, n_max + 1)],
                range=[0.5, n_max + 0.5]
            ),
            yaxis=dict(
                tickvals=list(range(1, n_max + 1)),
                ticktext=[str(i) for i in range(1, n_max + 1)],
                range=[0.5, n_max + 0.5]
            ),
            zaxis=dict(nticks=6),
            aspectmode="cube",
            camera=dict(
                eye=dict(
                    x=np.cos(np.deg2rad(135)) * 1.8,
                    y=np.sin(np.deg2rad(225)) * 1.8,
                    z=np.sin(np.deg2rad(60)) * 1.5
                )
            )
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        height=620
    )

    st.plotly_chart(fig)


def init_quantum_database():
    """
    预计算所有64种量子态 (n=1..4) 的波函数形状。
    基于 L=1 的单位立方体计算。
    """
    if 'wavefunction_db' in st.session_state:
        return None

    # loading 提示，因为第一次打开需要运算这64组数据 (约0.5秒)
    with st.spinner('Pre-calculating quantum states database...'):
        resolution = 30
        # 1. 生成标准单位坐标 (0 到 1)
        x_std = np.linspace(0, 1, resolution)
        y_std = np.linspace(0, 1, resolution)
        z_std = np.linspace(0, 1, resolution)
        X_std, Y_std, Z_std = np.meshgrid(x_std, y_std, z_std, indexing='ij')

        # 存入 session 用于后续线性变换
        st.session_state['grid_std'] = (X_std.flatten(), Y_std.flatten(), Z_std.flatten())

        # 2. 预计算 64 种组合的 psi (不含体积系数，仅形状)
        # Standard Psi shape = sin(nx*pi*x) * sin(ny*pi*y) * sin(nz*pi*z)
        db = {}
        for nx in range(1, 5):
            for ny in range(1, 5):
                for nz in range(1, 5):
                    # 这里的计算只在初始化时发生一次
                    psi_shape = (np.sin(nx * np.pi * X_std) *
                                 np.sin(ny * np.pi * Y_std) *
                                 np.sin(nz * np.pi * Z_std)).flatten()
                    db[(nx, ny, nz)] = psi_shape

        st.session_state['wavefunction_db'] = db


def display_3d_infinite_well():
    st.set_page_config(page_title="3D Infinite Well", layout="wide")

    # 初始化数据库 (如果已存在则直接跳过)
    init_quantum_database()

    st.title(':red[3D] Infinite Square Well')

    # Sidebar parameter selection
    with st.sidebar:
        st.header('Formulas')
        st.latex(r"""\Psi_{n_x,n_y,n_z}(x, y, z) = \sqrt{\frac{8}{L_x L_y L_z}} \
        \sin\left(\frac{n_x\pi x}{L_x}\right) \sin\left(\frac{n_y\pi y}{L_y}\right) \
        \sin\left(\frac{n_z\pi z}{L_z}\right)""")
        st.latex(r"""E_{n_x, n_y, n_z} = \frac{\pi^2\hbar^2}{2m_e} \left(
            \frac{n_x^2}{L_x^2} + \frac{n_y^2}{L_y^2} + \frac{n_z^2}{L_z^2}\right)""")
        st.header('Set parameters')
        n_x = st.slider('Quantum number in $x$ $(n_x)$', 1, 4, 1, step=1)
        n_y = st.slider('Quantum number in $y$ $(n_y)$', 1, 4, 1, step=1)
        n_z = st.slider('Quantum number in $z$ $(n_z)$', 1, 4, 1, step=1)
        L_x = st.slider('Length in $x$ $(L_x)$', 1.0, 4.0, 1.0, step=0.25)
        L_y = st.slider('Length in $y$ $(L_y)$', 1.0, 4.0, 1.0, step=0.25)
        L_z = st.slider('Length in $z$ $(L_z)$', 1.0, 4.0, 1.0, step=0.25)
        st.button(label="←—— back to home", on_click=goto_page, args=("Home",))

    # 获取标准网格
    X_flat, Y_flat, Z_flat = st.session_state['grid_std']

    # 线性变换：直接拉伸坐标轴 (Linear Transformation)
    # 向量乘法比重新 meshgrid + sin 快得多
    X_real = X_flat * L_x
    Y_real = Y_flat * L_y
    Z_real = Z_flat * L_z

    # 查表获取波形
    psi_shape = st.session_state['wavefunction_db'][(n_x, n_y, n_z)]

    # 幅值修正 (Normalization)
    # 标准箱(L=1)系数是 sqrt(8)。新箱子系数是 sqrt(8 / V)。
    # 比例因子 = sqrt(1 / (Lx*Ly*Lz))
    volume = L_x * L_y * L_z
    amp_scale = np.sqrt(8.0 / volume)

    psi_real = psi_shape * amp_scale
    psi2_real = psi_real ** 2

    # 绘图

    # === 绘制 fig1: 单层波函数等值面 ===

    # 1. 确定阈值：取最大幅值的 15% 作为等值面边界
    max_amp = np.max(np.abs(psi_real))
    threshold = max_amp * 0.15

    fig1 = go.Figure()

    # 2. 绘制正相位面 (红色)
    # 逻辑：只画 value == +threshold 的那一个面
    fig1.add_trace(go.Isosurface(
        x=X_real, y=Y_real, z=Z_real,
        value=psi_real,
        isomin=threshold,  # 最小值
        isomax=threshold,  # 最大值设为相同
        surface_count=1,  # 强制只画一层
        caps=dict(x_show=False, y_show=False, z_show=False),  # 不封口，看内部结构
        colorscale=[[0, 'rgb(165, 0, 38)'], [1, 'rgb(165, 0, 38)']],  # 纯红，无渐变
        showscale=False,  # 隐藏右侧颜色条，因为只有一种颜色
        name='Positive (+)'
    ))

    # 3. 绘制负相位面 (蓝色) - 仅当存在负值时 (n > 1)
    if psi_real.min() < 0:
        fig1.add_trace(go.Isosurface(
            x=X_real, y=Y_real, z=Z_real,
            value=psi_real,
            isomin=-threshold,  # 负的阈值
            isomax=-threshold,  # 锁定在一个值
            surface_count=1,
            caps=dict(x_show=False, y_show=False, z_show=False),
            colorscale=[[0, 'rgb(49, 54, 149)'], [1, 'rgb(49, 54, 149)']],  # 纯蓝
            showscale=False,
            name='Negative (-)'
        ))

    common_layout = dict(
        scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z', aspectmode='cube'),
        margin=dict(l=5, r=10, b=10, t=40),
        height=800
    )

    fig1.update_layout(title={'text': 'Wavefunction', 'x': 0.5}, **common_layout)

    fig2 = go.Figure(
        data=go.Isosurface(
            x=X_real, y=Y_real, z=Z_real,
            value=psi2_real,
            isomin=psi2_real.max() * 0.1,
            isomax=psi2_real.max(),
            surface_count=4,
            opacity=0.8,
            caps=dict(x_show=False, y_show=False, z_show=False),
            colorscale='Viridis',
            colorbar_title='Density'
        )
    )
    fig2.update_layout(title={'text': 'Probability Density', 'x': 0.4}, **common_layout)

    c1, c2 = st.columns(2, gap="large")
    with c1: st.plotly_chart(fig1, use_container_width=True)
    with c2: st.plotly_chart(fig2, use_container_width=True)


if "page" not in st.session_state:
    st.session_state.page = "Home"

def goto_page(page):
    st.session_state.page = page

if st.session_state.page == "Home":
    homepage()
if st.session_state.page == "1D":
    display_1d_infinite_well()
if st.session_state.page == "2D":
    display_2d_infinite_well()
if st.session_state.page == "3D":
    display_3d_infinite_well()

