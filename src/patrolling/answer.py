import time
import math
import random
#random.seed(0)

start_time=time.time()

debug=0

if debug:
  import sys
  import os
  f = open('input.txt', 'r', encoding="utf-8_sig")
  sys.stdin = f
else:
  from sys import stdin
  input=lambda :stdin.readline()[:-1]
  
N,startx,starty=map(int,input().split())
C=[0]*N*N
for i in range(N):
  ci=input()
  for j in range(N):
    if ci[j]=='#':
      C[N*i+j]=-1
    else:
      C[N*i+j]=int(ci[j])

road=[]
for x in range(0,N,2):
  y=0
  while True:
    if y==N:
      break
    if C[x*N+y]==-1:
      y+=1
    else:
      if y==N-1 or C[x*N+(y+1)]==-1:
        y+=1
      else:
        L=y
        while y!=N and C[x*N+y]!=-1:
          y+=1
        road.append((0,x,L,x,y-1))

for y in range(0,N,2):
  x=0
  while True:
    if x==N:
      break
    if C[x*N+y]==-1:
      x+=1
    else:
      if x==N-1 or C[(x+1)*N+y]==-1:
        x+=1
      else:
        U=x
        while x!=N and C[x*N+y]!=-1:
          x+=1
        road.append((1,U,y,x-1,y))

road.append((0,startx,starty,startx,starty))
intersects=[(startx,starty)]
intersect_id=[[-1]*N for i in range(N)]
intersect_of_road=[]
intersect_id[startx][starty]=0
intersect_cnt=1
num_of_intersect=[]
offset=[]

for t,x1,y1,x2,y2 in road:
  offset.append(len(intersect_of_road))
  tmp_size=0
  if x1==x2 and y1==y2:
    tmp_size+=1
    intersect_of_road.append(intersect_id[x1][y1])
    num_of_intersect.append(tmp_size)
    continue
  if t==0:
    for i in range(y1,y2+1):
      flag=False
      if x1>0 and C[(x1-1)*N+i]!=-1:
        flag=True
      if x1<N-1 and C[(x1+1)*N+i]!=-1:
        flag=True
      if flag:
        if intersect_id[x1][i]==-1:
          intersect_id[x1][i]=intersect_cnt
          intersects.append((x1,i))
          intersect_cnt+=1
        tmp_size+=1
        intersect_of_road.append(intersect_id[x1][i])
  else:
    for i in range(x1,x2+1):
      # assert C[i*N+y1]!=-1
      flag=False
      if y1>0 and C[i*N+(y1-1)]!=-1:
        flag=True
      if y1<N-1 and C[i*N+(y1+1)]!=-1:
        flag=True
      if flag:
        if intersect_id[i][y1]==-1:
          intersect_id[i][y1]=intersect_cnt
          intersects.append((i,y1))
          intersect_cnt+=1
        tmp_size+=1
        intersect_of_road.append(intersect_id[i][y1])
  num_of_intersect.append(tmp_size)

from heapq import heappop, heappush
dxdy=[(1,0),(0,1),(-1,0),(0,-1)]
IC=intersect_cnt
inf=1<<20
dist=[inf]*IC*IC
mask7=(1<<7)-1

for i in range(IC):
  x,y=intersects[i]
  hq=[(0<<14)|(x<<7)|y]
  tmp=[inf]*N*N
  tmp[x*N+y]=0
  while hq:
    res=heappop(hq)
    d=(res>>14)
    x=(res>>7)&mask7
    y=res&mask7
    if tmp[x*N+y]<d:
      continue
    for dx,dy in dxdy:
      nx,ny=x+dx,y+dy
      if 0<=nx<N and 0<=ny<N and C[nx*N+ny]!=-1 and d+C[nx*N+ny]<tmp[nx*N+ny]:
        tmp[nx*N+ny]=d+C[nx*N+ny]
        heappush(hq,(tmp[nx*N+ny]<<14)|(nx<<7)|ny)
  
  for j in range(IC):
    if i==j:
      dist[i*IC+j]=0
    else:
      x,y=intersects[j]
      dist[i*IC+j]=tmp[x*N+y]

RS=len(road)
road_dist_d=[inf]*RS*RS
road_dist_frm=[-1]*RS*RS
road_dist_to=[-1]*RS*RS

for i in range(RS):
  for j in range(RS):
    if i==j:
      continue
    num_i=num_of_intersect[i]
    num_j=num_of_intersect[j]
    for ii in range(num_i):
      for jj in range(num_j):
        frm=intersect_of_road[offset[i]+ii]
        to=intersect_of_road[offset[j]+jj]
        if dist[frm*IC+to]<road_dist_d[i*RS+j]:
          road_dist_d[i*RS+j]=dist[frm*IC+to]
          road_dist_frm[i*RS+j]=frm
          road_dist_to[i*RS+j]=to

first_perm=list(range(RS-1))
random.shuffle(first_perm)
now_ans=[RS-1]+first_perm+[RS-1]
IN=[-1]*(RS+1)
OUT=[-1]*(RS+1)

for i in range(RS):
  frm=now_ans[i]
  to=now_ans[i+1]
  OUT[i]=road_dist_frm[frm*RS+to]
  IN[i+1]=road_dist_to[frm*RS+to]

def calc_all_dist():
  res=0
  for i in range(RS):
    if i!=0:
      frm=IN[i]
      to=OUT[i]
      res+=dist[frm*IC+to]
    frm=OUT[i]
    to=IN[i+1]
    res+=dist[frm*IC+to]
  return res

now_dist=calc_all_dist()

def swap(temp):
  L=random.randint(0,RS-3)
  R=random.randint(L+3,RS)
  
  prev=0
  for i in range(L,R+1):
    if i!=0 and i!=RS:
      frm=IN[i]
      to=OUT[i]
      prev+=dist[frm*IC+to]
    if i!=R:
      frm=OUT[i]
      to=IN[i+1]
      prev+=dist[frm*IC+to]
  l=L+1
  r=R-1
  while l<r:
    now_ans[l],now_ans[r]=now_ans[r],now_ans[l]
    l+=1
    r-=1

  
  for i in range(L,R):
    frm=now_ans[i]
    to=now_ans[i+1]
    OUT[i]=road_dist_frm[frm*RS+to]
    IN[i+1]=road_dist_to[frm*RS+to]

  nxt=0
  for i in range(L,R+1):
    if i!=0 and i!=RS:
      frm=IN[i]
      to=OUT[i]
      nxt+=dist[frm*IC+to]
    if i!=R:
      frm=OUT[i]
      to=IN[i+1]
      nxt+=dist[frm*IC+to]
  
  diff=-prev+nxt
  if -diff>-10*temp and random.random()<math.exp(min(0,-diff/temp)):
    return diff
  l=L+1
  r=R-1
  while l<r:
    now_ans[l],now_ans[r]=now_ans[r],now_ans[l]
    l+=1
    r-=1
  
  for i in range(L,R):
    frm=now_ans[i]
    to=now_ans[i+1]
    OUT[i]=road_dist_frm[frm*RS+to]
    IN[i+1]=road_dist_to[frm*RS+to]
  return 0

def insert(temp):
  L=random.randint(1,RS-5)
  R=random.randint(L+4,RS-1)
  
  prev=0
  for i in range(L-1,R+2):
    if i!=0 and i!=RS:
      frm=IN[i]
      to=OUT[i]
      prev+=dist[frm*IC+to]
    if i!=R+1:
      frm=OUT[i]
      to=IN[i+1]
      prev+=dist[frm*IC+to]
  
  rev=0
  if random.random()<0.5:
    rev=1

  if rev==0:
    now_ans[L:R+1]=[now_ans[R]]+now_ans[L:R]
  else:
    now_ans[L:R+1]=now_ans[L+1:R+1]+[now_ans[L]]
  
  for i in range(L-1,R+1):
    frm=now_ans[i]
    to=now_ans[i+1]
    OUT[i]=road_dist_frm[frm*RS+to]
    IN[i+1]=road_dist_to[frm*RS+to]

  nxt=0
  for i in range(L-1,R+2):
    if i!=0 and i!=RS:
      frm=IN[i]
      to=OUT[i]
      nxt+=dist[frm*IC+to]
    if i!=R+1:
      frm=OUT[i]
      to=IN[i+1]
      nxt+=dist[frm*IC+to]

  diff=-prev+nxt
  if -diff>-10*temp and random.random()<math.exp(min(0,-diff/temp)):
    return diff
  if rev==1:
    now_ans[L:R+1]=[now_ans[R]]+now_ans[L:R]
  else:
    now_ans[L:R+1]=now_ans[L+1:R+1]+[now_ans[L]]
  
  for i in range(L-1,R+1):
    frm=now_ans[i]
    to=now_ans[i+1]
    OUT[i]=road_dist_frm[frm*RS+to]
    IN[i+1]=road_dist_to[frm*RS+to]
  return 0

    
SA_start=time.time()
SA_end=start_time+2.8

T0=40
T1=0.0001

def get_temp(Time):
  return T0+(Time-SA_start)*(T0-T1)/(SA_start-SA_end)


while True:
  now_time=time.time()
  if now_time>SA_end:
    break
  temp=get_temp(now_time)
  for _ in range(100):
    now_dist+=insert(temp)
    now_dist+=swap(temp)
  #print(now_dist)

def restore(frm,to):
  frm_x,frm_y=intersects[frm]
  to_x,to_y=intersects[to]
  
  par=[-1]*N*N
  tmp1=[inf]*N*N
  hq1=[(0<<14)|(to_x<<7)|to_y]
  tmp1[to_x*N+to_y]=0
  while hq1:
    res=heappop(hq1)
    d=(res>>14)
    x=(res>>7)&mask7
    y=res&mask7
    if tmp1[x*N+y]<d:
      continue
    if x==frm_x and y==frm_y:
      break
    for dir in range(4):
      dx,dy=dxdy[dir]
      nx,ny=x+dx,y+dy
      if 0<=nx<N and 0<=ny<N and C[nx*N+ny]!=-1 and d+C[nx*N+ny]<tmp1[nx*N+ny]:
        tmp1[nx*N+ny]=d+C[nx*N+ny]
        par[nx*N+ny]=dir
        heappush(hq1,(tmp1[nx*N+ny]<<14)|(nx<<7)|ny)

  now_x,now_y=frm_x,frm_y
  while now_x!=to_x or now_y!=to_y:
    dir=par[now_x*N+now_y]
    assert dir!=-1
    dx,dy=dxdy[dir]
    dx=-dx
    dy=-dy
    now_x+=dx
    now_y+=dy
    if dx==0 and dy==1:
      ans_str.append('R')
    if dx==0 and dy==-1:
      ans_str.append('L')
    if dx==1 and dy==0:
      ans_str.append('D')
    if dx==-1 and dy==0:
      ans_str.append('U')

ans_str=[]
for i in range(RS):
  if i!=0:
    frm=IN[i]
    to=OUT[i]
    restore(frm,to)

  frm=OUT[i]
  to=IN[i+1]
  restore(frm,to)

print(''.join(ans_str))