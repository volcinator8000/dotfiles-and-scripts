import cairo, math, random, os
random.seed(23)
W,H = 3840,2160
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
def hexc(h,a=1):
    h=h.lstrip('#'); return (int(h[0:2],16)/255,int(h[2:4],16)/255,int(h[4:6],16)/255,a)
BLUE='#3ae0ff'; PURPLE='#a64dff'; PINK='#ff5cc8'; RED='#ff2d3a'; BG='#050507'
c.set_source_rgba(*hexc(BG)); c.paint()
c.set_line_cap(cairo.LINE_CAP_BUTT); c.set_line_join(cairo.LINE_JOIN_MITER); c.set_miter_limit(40)
cx,cy = W/2,H/2

def stroke_glow(path_fn,color,width,alpha):
    for w,a in ((width*7,alpha*0.05),(width*3,alpha*0.14),(width,alpha)):
        c.set_source_rgba(*hexc(color,a)); c.set_line_width(w); path_fn(); c.stroke()

def thorn(x,y,ang,length,base_w,color,alpha):
    """filled tapered thorn (triangle with slight concave sides) -> sharp tip"""
    tx,ty = x+math.cos(ang)*length, y+math.sin(ang)*length
    nx,ny = -math.sin(ang)*base_w/2, math.cos(ang)*base_w/2
    def p():
        c.move_to(x+nx,y+ny)
        c.curve_to(x+nx*0.3+math.cos(ang)*length*0.5, y+ny*0.3+math.sin(ang)*length*0.5, tx,ty, tx,ty)
        c.curve_to(x-nx*0.3+math.cos(ang)*length*0.5, y-ny*0.3+math.sin(ang)*length*0.5, x-nx,y-ny, x-nx,y-ny)
        c.close_path()
    for grow,a in ((8,alpha*0.05),(3,alpha*0.12),(0,alpha)):
        c.set_source_rgba(*hexc(color,a)); p()
        if grow: c.set_line_width(grow); c.stroke()
        else: c.fill()
    return tx,ty

def spine(x,y,ang,length,color,alpha,width=1.8,segs=4,depth=0):
    """angular kinked spine with thorns off each joint, tapering to a tip"""
    pts=[(x,y)]; a=ang; px,py=x,y
    for i in range(segs):
        seg = length*random.uniform(0.18,0.32)
        a += random.uniform(-0.28,0.28)
        px,py = px+math.cos(a)*seg, py+math.sin(a)*seg
        pts.append((px,py))
    def path():
        c.move_to(*pts[0])
        for q in pts[1:]: c.line_to(*q)
    stroke_glow(path,color,width,alpha)
    # thorns at joints, alternating sides, shrinking outward
    for i in range(1,len(pts)):
        jx,jy = pts[i]; side = 1 if i%2 else -1
        seg_ang = math.atan2(pts[i][1]-pts[i-1][1], pts[i][0]-pts[i-1][0])
        tl = length*random.uniform(0.10,0.22)*(1-i/(len(pts)+1))
        tx,ty = thorn(jx,jy, seg_ang+side*random.uniform(0.9,1.5), tl, width*2.2, color, alpha*0.9)
        if depth<1 and random.random()<0.5:
            spine(tx,ty, seg_ang+side*random.uniform(0.6,1.2), tl*1.6, color, alpha*0.7, width*0.6, 3, depth+1)
    # final tip thorn
    tip_ang = math.atan2(pts[-1][1]-pts[-2][1], pts[-1][0]-pts[-2][0])
    thorn(pts[-1][0],pts[-1][1], tip_ang, length*0.18, width*2.4, color, alpha)
    return pts[-1]

def ring(x,y,r,color,alpha,w=1.4,ticks=0):
    stroke_glow(lambda: c.arc(x,y,r,0,2*math.pi), color, w, alpha)
    if ticks:
        c.set_line_width(1.2)
        for k in range(ticks):
            a=k/ticks*2*math.pi; r1=r+(22 if k%(ticks//8)==0 else 8)
            c.set_source_rgba(*hexc(color,alpha*(0.9 if k%(ticks//8)==0 else 0.45)))
            c.move_to(x+math.cos(a)*r,y+math.sin(a)*r); c.line_to(x+math.cos(a)*r1,y+math.sin(a)*r1); c.stroke()

# ── central sigil: bilateral, angular ──
arms=[(-90,1.25),(-62,0.8),(-38,1.0),(-14,0.7),(10,1.05),(34,0.75),(58,0.95),(90,1.2)]
for deg,mult in arms:
    ang=math.radians(deg); ln=560*mult*random.uniform(0.9,1.1)
    color = BLUE if random.random()<0.7 else random.choice([PURPLE,PINK])
    st = random.getstate()
    for mirror in (1,-1):
        random.setstate(st)
        c.save(); c.translate(cx,cy); c.scale(mirror,1); c.translate(-cx,-cy)
        r0 = 120
        spine(cx+math.cos(ang)*r0, cy+math.sin(ang)*r0, ang, ln, color, 0.95)
        c.restore()
# core
ring(cx,cy,120,BLUE,0.9,1.4,48)
ring(cx,cy,84,PURPLE,0.55,1.0)
ring(cx,cy,40,BLUE,0.9,1.4)
for k in range(6):
    a=k/6*2*math.pi
    thorn(cx+math.cos(a)*40, cy+math.sin(a)*40, a, 34, 9, BLUE, 0.9)
c.set_source_rgba(*hexc(RED,0.18)); c.arc(cx,cy,22,0,2*math.pi); c.fill()
stroke_glow(lambda: c.arc(cx,cy,12,0,2*math.pi), RED, 1.6, 1.0)
# vertical hairline through the sigil (chrome axis)
c.set_source_rgba(*hexc(BLUE,0.25)); c.set_line_width(1)
c.move_to(cx,cy-980); c.line_to(cx,cy-140); c.stroke(); c.move_to(cx,cy+140); c.line_to(cx,cy+980); c.stroke()

# ── satellite glyphs in the corners ──
for (px,py) in ((380,330),(W-420,300),(340,H-360),(W-380,H-330),(W/2-1200,H/2),(W/2+1200,H/2)):
    col = random.choice([BLUE,PURPLE,PINK,BLUE])
    n=random.choice([3,4,5]); base=random.uniform(0,math.pi)
    for j in range(n):
        spine(px,py, base+j*2*math.pi/n, random.uniform(110,200), col, 0.55, 1.1, 3, 1)
    ring(px,py,10,col,0.7,1.0)

# scanlines
c.set_source_rgba(1,1,1,0.016); c.set_line_width(1)
for y in range(0,H,4): c.move_to(0,y); c.line_to(W,y); c.stroke()
s.write_to_png(os.path.expanduser('~/Pictures/Wallpapers/cybersigil_raw.png'))
