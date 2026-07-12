/**
 * PARMADTIC — game.js
 * Alpine component for the crash-game widget.
 * Registered via Alpine.data() so it's decoupled from load order
 * and safe to defer/bundle however the app's build pipeline wants.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('gameApp', () => ({

        // ---------------- Core game state ----------------
        isAuthenticated: false,   // set from template on x-init
        ws: null,
        status: 'WAITING',
        multiplier: '1.00',
        countdown: '5.0',
        roundId: null,
        recentHistory: [],
        balance: '0',
        betAmount: 10000,
        betId: null,
        isBetPlaced: false,
        sysMessage: 'Simulator Siap.',
        cashoutTarget: '',
        activePlayers: 0,

        // ---------------- Modal / history pagination ----------------
        isModalOpen: false,
        fullHistoryData: [],
        currentPage: 1,
        hasNextPage: false,
        isLoadingHistory: false,

        // ---------------- Rocket → Moon crash trajectory ----------------
        crashOffset: { x: 0, y: 0 },
        moonImpact: false,
        stageNoTransition: false,

        // ---------------- Audio ----------------
        audioUnlocked: false,
        isMuted: false,

      init() {
    this.connectWebSocket();
    this.$nextTick(() => {

        const nav = document.getElementById("global-balance-display");

        if (nav) {

            nav.innerText = "Rp " + this.formatRupiah(this.balance);

        }

    });
    this.$watch('status', (val) => {

    if (val === 'CRASHED')
        this.flyToMoon();

    if (val === 'WAITING')
        this.resetStage();

});

    // Coba autoplay saat halaman dibuka
    this.$nextTick(() => {
        const bgm = this.$refs.bgm;

        if (!bgm) return;

        bgm.volume = 0.40;

        bgm.play()
            .then(() => {
                this.audioUnlocked = true;
            })
            .catch(() => {
                // Browser memblokir autoplay.
                // Musik akan mulai saat klik pertama di halaman.
                const startMusic = () => {
                    bgm.play().then(() => {
                        this.audioUnlocked = true;
                    }).catch(() => {});

                    document.removeEventListener('pointerdown', startMusic);
                };

                document.addEventListener('pointerdown', startMusic, { once: true });
            });
    });
},

        // ================= AUTH GATE =================
        requireAuth(event) {
            if (!this.isAuthenticated) {
                event.preventDefault();
                event.stopPropagation();

                Swal.fire({
                    title: 'Akses Terbatas',
                    text: 'Silakan masuk atau daftar akun terlebih dahulu untuk bisa memasang taruhan.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Login Sekarang',
                    cancelButtonText: 'Nanti Saja',
                    confirmButtonColor: '#2563eb'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = this.loginUrl || '/login/';
                    }
                });
            }
        },

        // ================= WEBSOCKET =================
        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            this.ws = new WebSocket(protocol + window.location.host + '/ws/game/');

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'game_tick') {
                    this.status = data.payload.state;
                    this.roundId = data.payload.round_id;
                    if (data.payload.history) { this.recentHistory = data.payload.history; }

                    if (data.payload.active_players !== undefined) {
                        this.activePlayers = data.payload.active_players;
                    }

                    if (this.status === 'WAITING') {
                        this.countdown = data.payload.countdown;
                    } else if (this.status === 'FLYING') {
                        this.multiplier = data.payload.multiplier;

                        if (this.isBetPlaced && this.cashoutTarget) {
                            if (parseFloat(this.multiplier) >= parseFloat(this.cashoutTarget)) {
                                this.cashoutFull();
                            }
                        }
                    } else if (this.status === 'CRASHED') {
                        this.multiplier = data.payload.multiplier;

                        if (this.isBetPlaced) {
                            this.isBetPlaced = false;
                            Swal.fire({
                                title: 'ROKET HANCUR!',
                                text: 'Anda kehilangan taruhan.',
                                icon: 'error',
                                confirmButtonColor: '#ef4444',
                                timer: 2000
                            }).then(() => window.location.reload());
                        }
                    }
                }

                else if (data.type === 'bet_success') {
                    this.isBetPlaced = true;
                    this.betId = data.bet_id;
                    this.updateBalanceDisplay(data.amount, 'deduct');
                    Swal.fire({ title: 'Berhasil!', text: 'Taruhan Rp ' + data.amount + ' dipasang.', icon: 'success', toast: true, position: 'top-end', showConfirmButton: false, timer: 2000 });
                }

                else if (data.type === 'cancel_success') {
                    this.isBetPlaced = false;
                    this.updateBalanceDisplay(this.betAmount, 'add');
                    Swal.fire({ title: 'Dibatalkan', text: 'Taruhan ditarik kembali.', icon: 'info', toast: true, position: 'top-end', showConfirmButton: false, timer: 2000 });
                }

                else if (data.type === 'cashout_success') {
                    this.isBetPlaced = false;
                    this.updateBalanceDisplay(data.profit, 'add');
                   Swal.fire({
    title: 'MENANG PROFIT!',
    text: 'Mendapatkan Rp ' + new Intl.NumberFormat('id-ID').format(Number(data.profit)),
    icon: 'success',
    confirmButtonColor: '#10b981',
    timer: 2500
});
                }

                else if (data.type === 'cashout_half_success') {
                    this.betAmount = this.betAmount / 2;
                    this.updateBalanceDisplay(data.profit, 'add');
                    Swal.fire({
                        title: 'Cair 50%',
                        text: 'Sebagian profit diamankan: Rp ' + new Intl.NumberFormat('id-ID').format(Number(data.profit)),
                        icon: 'success',
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 2000
                    });
                }

                else if (data.type === 'error') {
                    this.sysMessage = `Error: ${data.message}`;
                    setTimeout(() => this.sysMessage = 'Simulator Siap.', 3000);

                    Swal.fire({
                        title: 'Gagal!',
                        text: data.message,
                        icon: 'error',
                        confirmButtonColor: '#ef4444'
                    });
                }
            };

            this.ws.onclose = () => { setTimeout(() => this.connectWebSocket(), 3000); };
        },

        // ================= PLAYER ACTIONS =================
        placeBet() {
            if (parseFloat(this.betAmount) > parseFloat(this.balance)) {
                Swal.fire({
                    title: 'Saldo Tidak Cukup!',
                    text: 'Saldo dompet Anda kurang untuk nominal taruhan ini. Silakan Top-Up.',
                    icon: 'warning',
                    confirmButtonText: 'Isi Saldo',
                    confirmButtonColor: '#2563eb',
                    showCancelButton: true,
                    cancelButtonText: 'Batal'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = this.depositUrl || '/deposit/';
                    }
                });
                return;
            }

            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ action: 'bet', amount: this.betAmount.toString(), round_id: this.roundId }));
            }
        },
        cancelBet() {
    console.log("Cancel Bet", this.betId);

    this.ws.send(JSON.stringify({
        action: 'cancel_bet',
        bet_id: this.betId
    }));
},
        cashoutFull() { this.ws.send(JSON.stringify({ action: 'cashout', bet_id: this.betId, multiplier: this.multiplier.toString() })); },
        cashoutHalf() { this.ws.send(JSON.stringify({ action: 'cashout_half', bet_id: this.betId, multiplier: this.multiplier.toString() })); },

        updateBalanceDisplay(amount, action) {

            let currentBal = Number(this.balance);
            let modifier = Number(amount);

            if (action === "add") {
                currentBal += modifier;
            } else {
                currentBal -= modifier;
            }

            this.balance = currentBal;

            const nav = document.getElementById("global-balance-display");

            if (nav) {
                nav.innerText = "Rp " + this.formatRupiah(currentBal);
            }
            
            const page = document.getElementById("page-balance");

            if (page) {
                page.innerText = "Rp " + this.formatRupiah(currentBal);
            }

        },

        // ================= HISTORY MODAL =================
        openModal() { this.isModalOpen = true; this.fullHistoryData = []; this.currentPage = 1; this.fetchHistory(); },
        closeModal() { this.isModalOpen = false; },
        fetchHistory() {
            this.isLoadingHistory = true;
            fetch(`/api/history/?page=${this.currentPage}`).then(r => r.json()).then(data => {
                this.fullHistoryData = [...this.fullHistoryData, ...data.history];
                this.hasNextPage = data.has_next;
                this.isLoadingHistory = false;
            });
        },
        loadMoreHistory() { if (this.hasNextPage) { this.currentPage++; this.fetchHistory(); } },

        // ================= ROCKET → MOON CRASH TRAJECTORY =================
        // Measures real on-screen distance between the rocket stage and the
        // moon, then animates the stage there via CSS transition. Works at
        // any viewport size since it's computed, not hard-coded.
        async flyToMoon() {
            await this.$nextTick();
            if (!this.$refs.rocketStage || !this.$refs.moon) return;

            const rocketRect = this.$refs.rocketStage.getBoundingClientRect();
            const moonRect = this.$refs.moon.getBoundingClientRect();

            const rocketCenterX = rocketRect.left + rocketRect.width / 2;
            const rocketCenterY = rocketRect.top + rocketRect.height / 2;
            const moonCenterX = moonRect.left + moonRect.width / 2;
            const moonCenterY = moonRect.top + moonRect.height / 2;

            this.crashOffset = {
                x: moonCenterX - rocketCenterX,
                y: moonCenterY - rocketCenterY,
            };

            // Impact flash + moon rattle timed to the CSS transition (0.38s)
            setTimeout(() => { this.moonImpact = true; }, 360);
            setTimeout(() => { this.moonImpact = false; }, 900);
        },

        resetStage() {
            // Snap back instantly (no fly-back animation) so the rocket is
            // ready and centered before the next round's countdown starts.
            this.stageNoTransition = true;
            this.crashOffset = { x: 0, y: 0 };
            this.moonImpact = false;
            requestAnimationFrame(() => {
                requestAnimationFrame(() => { this.stageNoTransition = false; });
            });
        },

//         // ================= AUDIO =================
//         unlockAudio() {
//     this.audioUnlocked = true;

//     this.$refs.bgm.volume = 0.25;
//     this.$refs.bgm.play().catch(() => {});
// },
//        toggleMute() {
//     this.isMuted = !this.isMuted;
//     this.$refs.bgm.muted = this.isMuted;
// },
//         playTrackForStatus(status) {
//             if (!this.audioUnlocked) return;
//             const waiting = this.$refs.bgmWaiting;
//             const flying = this.$refs.bgmFlying;
//             const crashSfx = this.$refs.sfxCrash;
//             if (!waiting || !flying || !crashSfx) return;

//             if (status === 'WAITING') {
//                 flying.pause();
//                 waiting.currentTime = 0;
//                 waiting.play().catch(() => {});
//             } else if (status === 'FLYING') {
//                 waiting.pause();
//                 flying.currentTime = 0;
//                 flying.play().catch(() => {});
//             } else if (status === 'CRASHED') {
//                 waiting.pause();
//                 flying.pause();
//                 crashSfx.currentTime = 0;
//                 crashSfx.play().catch(() => {});
//             }
//         },

unlockAudio() {
    const bgm = this.$refs.bgm;

    if (!bgm) return;

    bgm.volume = 0.25;

    bgm.play().then(() => {
        this.audioUnlocked = true;
    }).catch(() => {});
},

toggleMute() {
    this.isMuted = !this.isMuted;

    if (this.$refs.bgm) {
        this.$refs.bgm.muted = this.isMuted;
    }
},
formatRupiah(value) {
    return new Intl.NumberFormat("id-ID", {
        maximumFractionDigits: 0
    }).format(Number(value));
},

        // ================= VISUAL HELPERS =================
        getColorClass(multiplier) {
            const cp = parseFloat(multiplier);
            if (cp < 2) return 'bg-slate-700 text-white font-bold border border-slate-500 shadow-md shadow-slate-900/50';
            if (cp < 5) return 'bg-blue-700 text-white font-bold border border-blue-500 shadow-md shadow-blue-900/50';
            if (cp < 10) return 'bg-violet-700 text-white font-bold border border-violet-500 shadow-md shadow-violet-900/50';
            if (cp < 25) return 'bg-fuchsia-700 text-white font-bold border border-fuchsia-500 shadow-md shadow-fuchsia-900/50';
            if (cp < 50) return 'bg-red-700 text-white font-bold border border-red-500 shadow-md shadow-red-900/50';
            if (cp < 100) return 'bg-orange-600 text-white font-bold border border-orange-400 shadow-md shadow-orange-900/50';
            return 'bg-yellow-400 text-black font-extrabold border border-yellow-300 shadow-lg shadow-yellow-500/60';
        },

        getBackgroundClass() {
            if (this.status === 'WAITING') return 'bg-slate-900 border-slate-700';
            if (this.status === 'CRASHED') return 'bg-red-950 border-red-700 shadow-[inset_0_0_180px_rgba(239,68,68,.4)]';

            const cp = parseFloat(this.multiplier);
            if (cp < 2) return 'bg-[#081221] border-slate-700';
            if (cp < 5) return 'bg-[#071B34] border-blue-600';
            if (cp < 10) return 'bg-[#120B34] border-violet-600';
            if (cp < 25) return 'bg-[#260B3D] border-fuchsia-600';
            if (cp < 50) return 'bg-[#3A0715] border-red-600';
            if (cp < 100) return 'bg-[#3E1A02] border-orange-500';
            return 'bg-[#493300] border-yellow-400';
        },

        getWarpSpeed() {
            const cp = parseFloat(this.multiplier);
            if (cp < 2) return '.8s';
            if (cp < 5) return '.6s';
            if (cp < 10) return '.45s';
            if (cp < 25) return '.35s';
            if (cp < 50) return '.25s';
            return '.15s';
        },

        getStarSpeed(layer) {
            const base = layer === 'near' ? 5 : 11;
            if (this.status !== 'FLYING') return base + 's';
            const cp = parseFloat(this.multiplier);
            const factor = Math.max(0.18, 1 - Math.min(cp, 60) / 65);
            return (base * factor).toFixed(2) + 's';
        },

        getWorldShakeClass() {
            if (this.status === 'CRASHED') return 'world-shake-crash';
            if (this.status !== 'FLYING') return '';
            const cp = parseFloat(this.multiplier);
            if (cp < 5) return '';
            if (cp < 15) return 'world-shake-1';
            if (cp < 40) return 'world-shake-2';
            return 'world-shake-3';
        },

        getBackgroundGlow() {
            if (this.status !== 'FLYING') return '';
            const cp = parseFloat(this.multiplier);
            if (cp < 2) return 'bg-gradient-to-br from-sky-700/20 via-transparent to-slate-900';
            if (cp < 5) return 'bg-gradient-to-br from-blue-600/30 via-transparent to-slate-900';
            if (cp < 10) return 'bg-gradient-to-br from-violet-600/35 via-transparent to-slate-900';
            if (cp < 25) return 'bg-gradient-to-br from-fuchsia-600/35 via-transparent to-slate-900';
            if (cp < 50) return 'bg-gradient-to-br from-red-600/35 via-transparent to-slate-900';
            if (cp < 100) return 'bg-gradient-to-br from-orange-500/40 via-transparent to-slate-900';
            return 'bg-gradient-to-br from-yellow-400/45 via-transparent to-slate-900';
        },

        getRocketGlow() {
            if (this.status !== 'FLYING') return 'bg-blue-500/20';
            const cp = parseFloat(this.multiplier);
            if (cp < 2) return 'bg-sky-500';
            if (cp < 5) return 'bg-blue-500';
            if (cp < 10) return 'bg-violet-500';
            if (cp < 25) return 'bg-fuchsia-500';
            if (cp < 50) return 'bg-red-500';
            if (cp < 100) return 'bg-orange-500';
            return 'bg-yellow-400 animate-pulse';
        },

        getNebulaLeft() {
            const cp = parseFloat(this.multiplier);
            if (cp < 2) return 'bg-blue-500';
            if (cp < 5) return 'bg-cyan-500';
            if (cp < 10) return 'bg-violet-500';
            if (cp < 25) return 'bg-fuchsia-500';
            if (cp < 50) return 'bg-red-500';
            if (cp < 100) return 'bg-orange-500';
            return 'bg-yellow-400';
        },

        getNebulaRight() {
            const cp = parseFloat(this.multiplier);
            if (cp < 2) return 'bg-slate-500';
            if (cp < 5) return 'bg-blue-700';
            if (cp < 10) return 'bg-indigo-700';
            if (cp < 25) return 'bg-purple-700';
            if (cp < 50) return 'bg-red-700';
            if (cp < 100) return 'bg-orange-700';
            return 'bg-amber-500';
        },
    }));
});