"""3D 등산코스 배경음악 만들기 → assets/3d/bgm.mp3

남의 음원을 쓰지 않으려고 곡을 코드로 직접 지어 합성한다(저작권 걱정 없음).
다장조, 빠르기 126, 48마디 약 1분 30초. numpy 와 ffmpeg 가 필요하다.

    python tools/make_bgm.py
"""
import os, subprocess, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
BPM = 126
BEAT = 60 / BPM
BAR = 4 * BEAT
N = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def hz(name):                       # 'E5' → 주파수
    return 440 * 2 ** ((N[name[0]] + 12 * (int(name[1]) + 1) - 69) / 12)


def env(n, a, d):                   # 빠르게 올라와 지수로 사라지는 소리 모양
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def pluck(f, dur, d=0.22):          # 마림바 비슷한 통통 튀는 음
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*4*f*t) * np.exp(-t/0.05)
            + 0.15*np.sin(2*np.pi*2*f*t)) * env(n, 0.004, d)


def strum(f, dur):                  # 우쿨렐레 느낌의 짧은 화음 음
    n = int(dur * SR); t = np.arange(n) / SR
    return sum(np.sin(2*np.pi*f*k*t) / k**1.6 for k in (1, 2, 3, 4)) * env(n, 0.003, 0.14)


def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*2*f*t)) * env(n, 0.008, 0.28)


def kick():
    n = int(0.22 * SR); t = np.arange(n) / SR
    return np.sin(2*np.pi*(48*t + 60*0.035*(1 - np.exp(-t/0.035)))) * np.exp(-t/0.09)


def noise(dur, d, seed):
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    return np.diff(x, prepend=0) * env(n, 0.002, d)          # 높은 소리만 남긴다


CH = {'C': ('C3', ['C4', 'E4', 'G4']), 'G': ('G2', ['B3', 'D4', 'G4']),
      'Am': ('A2', ['C4', 'E4', 'A4']), 'F': ('F2', ['C4', 'F4', 'A4']),
      'Em': ('E2', ['B3', 'E4', 'G4'])}
# 가락: (음, 박 길이). A 는 아르페지오로 통통, B 는 길게 노래하듯
MEL = {
 'A1': ['E5 G5 C6 G5 E5 G5 A5 G5', 'D5 G5 B5 G5 D5 G5 A5 B5',
        'C5 E5 A5 E5 C5 E5 G5 E5', 'F5 A5 C6 A5 G5 F5 E5 D5'],
 'A2': ['E5 G5 C6 G5 E5 G5 A5 G5', 'D5 G5 B5 G5 D5 G5 A5 B5',
        'C5 E5 A5 E5 C6 A5 G5 E5', 'F5 A5 C6 A5 B5 G5 D6 B5'],
 'B1': ['A5:1 C6:1 A5:1 F5:1', 'B5:1 D6:1 B5:1 G5:1', 'G5:1 B5:1 G5:1 E5:1', 'A5:2 E5:1 C5:1'],
 'B2': ['A5:1 C6:1 A5:1 F5:1', 'B5:1 D6:1 B5:1 G5:1', 'C6:2 G5:1 E5:1', 'C6:4'],
}
PROG = {'A1': ['C', 'G', 'Am', 'F'], 'A2': ['C', 'G', 'Am', 'F'],
        'B1': ['F', 'G', 'Em', 'Am'], 'B2': ['F', 'G', 'C', 'C'], 'I': ['C', 'G', 'Am', 'F']}
SONG = ['I', 'A1', 'A2', 'B1', 'B2', 'A1', 'A2', 'B1', 'B2', 'A1', 'A2', 'I']   # 4마디씩 48마디


def main():
    total = int((len(SONG) * 4 * BAR + 3) * SR)
    L = np.zeros(total); R = np.zeros(total)

    def add(sig, t, gain, pan=0.0):
        i = int(t * SR); j = min(total, i + len(sig)); s = sig[:j - i] * gain
        L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))

    for si, sec in enumerate(SONG):
        last = si == len(SONG) - 1
        for bi, ch in enumerate(PROG[sec]):
            t0 = (si * 4 + bi) * BAR
            root, tri = CH[ch]
            # 베이스: 근음-근음-5도-근음
            for k, (b, semis) in enumerate([(0, 0), (1.5, 0), (2, 7), (3, 0)]):
                add(bass(hz(root) * 2 ** (semis / 12), BEAT * 0.9), t0 + b * BEAT, 0.42)
            # 화음: 뒷박마다 살짝 흩어 뜯는다
            for b in (0.5, 1.5, 2.5, 3.5):
                for k, nm in enumerate(tri):
                    add(strum(hz(nm), 0.5), t0 + b * BEAT + k * 0.012, 0.13, pan=-0.45)
            # 타악기 (들머리 4마디는 셰이커만)
            for b in range(8):
                add(noise(0.08, 0.018, si * 100 + bi * 10 + b), t0 + b * BEAT / 2, 0.05 if b % 2 else 0.03, pan=0.4)
            if sec != 'I' or last:
                for b in (0, 2):
                    add(kick(), t0 + b * BEAT, 0.5)
                for b in (1, 3):
                    add(noise(0.16, 0.05, 7 + b), t0 + b * BEAT, 0.09)
            # 가락
            if sec in MEL:
                t = t0
                for tok in MEL[sec][bi].split():
                    nm, _, ln = tok.partition(':')
                    beats = float(ln) if ln else 0.5
                    add(pluck(hz(nm), beats * BEAT + 0.35, d=0.16 + 0.16 * beats), t, 0.30, pan=0.15)
                    t += beats * BEAT
    end = len(SONG) * 4 * BAR
    add(pluck(hz('C6'), 2.5, d=0.9), end, 0.3); add(bass(hz('C3'), 2.5), end, 0.4)
    for nm in ('C4', 'E4', 'G4'):
        add(strum(hz(nm), 2.0), end, 0.14)

    mix = np.stack([L, R], 1)
    d = int(0.75 * BEAT * SR)                                  # 가벼운 메아리
    mix[d:] += 0.18 * mix[:-d]
    mix /= np.abs(mix).max() / 0.89
    f_in, f_out = int(0.05 * SR), int(2.5 * SR)
    mix[:f_in] *= np.linspace(0, 1, f_in)[:, None]
    mix[-f_out:] *= np.linspace(1, 0, f_out)[:, None]

    wav = os.path.join(ROOT, 'assets', '3d', 'bgm.wav'); mp3 = wav[:-3] + 'mp3'
    with wave.open(wav, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-b:a', '112k', mp3], check=True)
    os.remove(wav)
    print(mp3, f'{total / SR:.0f}초, {os.path.getsize(mp3) // 1024}KB')


if __name__ == '__main__':
    main()
