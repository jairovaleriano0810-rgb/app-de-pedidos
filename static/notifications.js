// ==============================================
// SISTEMA DE NOTIFICACIONES CON SONIDO
// VERSIÓN CORREGIDA PARA MÓVIL (iOS + Android)
// ==============================================

class NotificationSystem {

    constructor() {
        this.lastOrderCount = 0;
        this.lastOrderStates = new Map();
        this.audioContext = null;
        this.notificationsEnabled = false;
        this.isPlayingSound = false;
        this.lastNotificationTime = 0;
        this.NOTIFICATION_COOLDOWN = 2000; // 2 segundos mínimo entre notificaciones
        this.processedOrderIds = new Set();

        this.init();
    }

    init() {
        // Solicitar permisos de notificación al cargar
        if ("Notification" in window && Notification.permission === "default") {
            this.requestPermission();
        }
        this.notificationsEnabled = ("Notification" in window) && Notification.permission === "granted";

        // Inicializar Audio Context
        this.initAudioContext();
    }

    // ==============================================
    // ✅ CORREGIDO: initAudioContext para móvil
    // Antes solo escuchaba 'click' (no funciona en touch iOS/Android)
    // Ahora escucha TAMBIÉN 'touchstart' y hace resume() si está suspendido
    // ==============================================
    initAudioContext() {
        const unlock = () => {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            // CRÍTICO para iOS Safari: el contexto arranca suspendido, hay que reanudarlo
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
        };

        // Escuchar tanto click (escritorio) como touchstart (móvil)
        document.addEventListener('click', unlock, { passive: true });
        document.addEventListener('touchstart', unlock, { passive: true });

        // También desbloquear cuando la página vuelve a ser visible
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.audioContext) {
                if (this.audioContext.state === 'suspended') {
                    this.audioContext.resume();
                }
            }
        });
    }

    requestPermission() {
        Notification.requestPermission().then(permission => {
            this.notificationsEnabled = permission === "granted";
            if (permission === "granted") {
                this.showWelcomeNotification();
            }
        });
    }

    showWelcomeNotification() {
        if (!("Notification" in window)) return;
        new Notification("🍽️ Sabor Ecuatoriano", {
            body: "Las notificaciones están activadas. Te avisaremos de nuevos pedidos y cambios de estado.",
            icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🍽️</text></svg>",
            badge: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🔔</text></svg>"
        });
    }

    // ==============================================
    // COOLDOWN Y PREVENCIÓN DE DUPLICADOS
    // ==============================================

    canPlayNotification() {
        const now = Date.now();
        if (this.isPlayingSound) {
            console.log('🔇 Sonido en reproducción, bloqueando nueva notificación');
            return false;
        }
        if (now - this.lastNotificationTime < this.NOTIFICATION_COOLDOWN) {
            console.log('🔇 Cooldown activo, bloqueando notificación');
            return false;
        }
        return true;
    }

    startNotification() {
        this.isPlayingSound = true;
        this.lastNotificationTime = Date.now();
    }

    endNotification() {
        setTimeout(() => {
            this.isPlayingSound = false;
        }, 500);
    }

    // ==============================================
    // ✅ CORREGIDO: playNewOrderSound — async + resume() antes de reproducir
    // En iOS el AudioContext puede estar 'suspended' aunque ya fue creado
    // ==============================================
    async playNewOrderSound() {
        if (!this.canPlayNotification()) return;

        this.startNotification();

        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            // CRÍTICO para iOS: siempre hacer resume() antes de usar el contexto
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            const ctx = this.audioContext;
            const now = ctx.currentTime;

            // Sonido alegre de "nuevo pedido" - melodía ascendente
            const notes = [
                { freq: 523.25, time: 0,    duration: 0.15 },  // C5
                { freq: 659.25, time: 0.15, duration: 0.15 },  // E5
                { freq: 783.99, time: 0.3,  duration: 0.25 }   // G5
            ];

            notes.forEach(note => {
                const osc = ctx.createOscillator();
                const gainNode = ctx.createGain();

                osc.connect(gainNode);
                gainNode.connect(ctx.destination);

                osc.frequency.value = note.freq;
                osc.type = 'sine';

                // Envelope
                gainNode.gain.setValueAtTime(0, now + note.time);
                gainNode.gain.linearRampToValueAtTime(0.3, now + note.time + 0.02);
                gainNode.gain.exponentialRampToValueAtTime(0.01, now + note.time + note.duration);

                osc.start(now + note.time);
                osc.stop(now + note.time + note.duration);
            });

            // Efecto de "ding" adicional
            setTimeout(() => {
                const osc = ctx.createOscillator();
                const gainNode = ctx.createGain();

                osc.connect(gainNode);
                gainNode.connect(ctx.destination);

                osc.frequency.value = 1046.50; // C6
                osc.type = 'sine';

                gainNode.gain.setValueAtTime(0.4, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);

                osc.start();
                osc.stop(ctx.currentTime + 0.5);

                this.endNotification();
            }, 450);

        } catch (err) {
            console.warn('⚠️ Error reproduciendo sonido de nuevo pedido:', err);
            this.endNotification();
        }
    }

    // ==============================================
    // ✅ CORREGIDO: playStatusChangeSound — async + resume() antes de reproducir
    // ==============================================
    async playStatusChangeSound() {
        if (!this.canPlayNotification()) return;

        this.startNotification();

        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            // CRÍTICO para iOS: siempre hacer resume() antes de usar el contexto
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            const ctx = this.audioContext;
            const now = ctx.currentTime;

            // Sonido suave de "actualización" - dos tonos armoniosos
            const notes = [
                { freq: 440,    time: 0,   duration: 0.2 },  // A4
                { freq: 554.37, time: 0.1, duration: 0.3 }   // C#5
            ];

            notes.forEach(note => {
                const osc = ctx.createOscillator();
                const gainNode = ctx.createGain();

                osc.connect(gainNode);
                gainNode.connect(ctx.destination);

                osc.frequency.value = note.freq;
                osc.type = 'triangle';

                gainNode.gain.setValueAtTime(0, now + note.time);
                gainNode.gain.linearRampToValueAtTime(0.2, now + note.time + 0.02);
                gainNode.gain.exponentialRampToValueAtTime(0.01, now + note.time + note.duration);

                osc.start(now + note.time);
                osc.stop(now + note.time + note.duration);
            });

            setTimeout(() => {
                this.endNotification();
            }, 400);

        } catch (err) {
            console.warn('⚠️ Error reproduciendo sonido de cambio de estado:', err);
            this.endNotification();
        }
    }

    // ==============================================
    // ✅ CORREGIDO: showBrowserNotification
    // Antes no verificaba si Notification API existe (falla en Safari iOS sin PWA)
    // ==============================================
    showBrowserNotification(title, body, icon = "🔔") {
        // En Safari iOS sin PWA, Notification API no existe o no funciona
        if (!("Notification" in window)) return;
        if (!this.notificationsEnabled) return;

        try {
            const notification = new Notification(title, {
                body: body,
                icon: `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>${icon}</text></svg>`,
                badge: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🔔</text></svg>",
                requireInteraction: false,
                tag: 'sabor-ecuatoriano'
            });

            // Auto cerrar después de 5 segundos
            setTimeout(() => notification.close(), 5000);

            // Al hacer click, enfocar la ventana
            notification.onclick = () => {
                window.focus();
                notification.close();
            };
        } catch (err) {
            console.warn('⚠️ No se pudo mostrar notificación del navegador:', err);
        }
    }

    // ==============================================
    // NOTIFICACIONES VISUALES EN PÁGINA (sin cambios, ya funcionaban)
    // ==============================================
    showInPageNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `in-page-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <strong>${title}</strong>
                <button onclick="this.parentElement.parentElement.remove()" class="close-notification">×</button>
            </div>
            <div class="notification-body">${message}</div>
        `;
        document.body.appendChild(notification);

        // Animar entrada
        setTimeout(() => notification.classList.add('show'), 10);

        // Auto remover después de 6 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 6000);
    }

    // ==============================================
    // DETECTORES DE CAMBIOS (sin cambios, ya funcionaban)
    // ==============================================
    checkForNewOrders(orders) {
        const currentCount = orders.length;

        // SOLO notificar si hay MÁS pedidos que antes
        if (this.lastOrderCount > 0 && currentCount > this.lastOrderCount) {
            const newOrdersCount = currentCount - this.lastOrderCount;

            // Obtener SOLO los pedidos nuevos (los que no hemos procesado)
            const newOrders = orders.slice(0, newOrdersCount).filter(order =>
                !this.processedOrderIds.has(order.id)
            );

            if (newOrders.length > 0) {
                console.log(`🆕 Detectados ${newOrders.length} pedidos nuevos reales`);

                const newOrder = newOrders[0]; // El pedido más reciente

                // Marcar como procesados
                newOrders.forEach(order => this.processedOrderIds.add(order.id));

                // Sonido (con cooldown)
                this.playNewOrderSound();

                // Notificación del navegador
                this.showBrowserNotification(
                    "🆕 Nuevo Pedido Recibido",
                    `Pedido #${newOrder.id} de ${newOrder.username || 'Cliente'}\nTotal: ${newOrders.length} nuevo${newOrders.length > 1 ? 's' : ''} pedido${newOrders.length > 1 ? 's' : ''}`,
                    "🛎️"
                );

                // Notificación en página
                this.showInPageNotification(
                    "🆕 Nuevo Pedido",
                    `<strong>Pedido #${newOrder.id}</strong> de <strong>${newOrder.username || 'Cliente'}</strong><br>
                    <small>${new Date(newOrder.timestamp).toLocaleTimeString('es-EC')}</small>`,
                    'success'
                );
            }
        }

        this.lastOrderCount = currentCount;
    }

    checkForStatusChanges(orders) {
        const statusNames = {
            'pending':   '⏳ Pendiente',
            'preparing': '🍳 Preparando',
            'ready':     '✅ Listo para recoger',
            'delivered': '🚀 Entregado'
        };

        let changesDetected = false;

        orders.forEach(order => {
            const lastStatus = this.lastOrderStates.get(order.id);

            // SOLO notificar si el estado CAMBIÓ de verdad
            if (lastStatus && lastStatus !== order.status) {
                console.log(`🔔 Estado cambió: Pedido #${order.id} de ${lastStatus} a ${order.status}`);

                changesDetected = true;

                // Notificación del navegador
                this.showBrowserNotification(
                    "🔔 Estado de Pedido Actualizado",
                    `Tu pedido #${order.id} ahora está: ${statusNames[order.status]}`,
                    "📦"
                );

                // Notificación en página
                this.showInPageNotification(
                    "🔔 Pedido Actualizado",
                    `<strong>Pedido #${order.id}</strong><br>
                    Nuevo estado: <strong>${statusNames[order.status]}</strong>`,
                    'info'
                );
            }

            // Actualizar el estado guardado
            this.lastOrderStates.set(order.id, order.status);
        });

        // Sonido SOLO si hubo cambios (con cooldown)
        if (changesDetected) {
            this.playStatusChangeSound();
        }
    }

    // Método para inicializar estados sin notificar
    initializeStates(orders) {
        console.log(`📋 Inicializando sistema con ${orders.length} pedidos`);
        this.lastOrderCount = orders.length;

        orders.forEach(order => {
            this.lastOrderStates.set(order.id, order.status);
            this.processedOrderIds.add(order.id); // Marcar como procesado
        });
    }
}

// Crear instancia global
window.notificationSystem = new NotificationSystem();