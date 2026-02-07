// ==============================================
// SISTEMA DE NOTIFICACIONES CON SONIDO
// ==============================================

class NotificationSystem {
    constructor() {
        this.lastOrderCount = 0;
        this.lastOrderStates = new Map();
        this.audioContext = null;
        this.notificationsEnabled = false;
        this.init();
    }

    init() {
        // Solicitar permisos de notificación al cargar
        if ("Notification" in window && Notification.permission === "default") {
            this.requestPermission();
        }
        this.notificationsEnabled = Notification.permission === "granted";
        
        // Inicializar Audio Context (se creará al primer sonido por políticas del navegador)
        this.initAudioContext();
    }

    initAudioContext() {
        // El contexto de audio se creará cuando el usuario interactúe
        document.addEventListener('click', () => {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
        }, { once: true });
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
        new Notification("🍽️ Sabor Ecuatoriano", {
            body: "Las notificaciones están activadas. Te avisaremos de nuevos pedidos y cambios de estado.",
            icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🍽️</text></svg>",
            badge: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🔔</text></svg>"
        });
    }

    // ==============================================
    // GENERADORES DE SONIDO
    // ==============================================

    playNewOrderSound() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        const ctx = this.audioContext;
        const now = ctx.currentTime;

        // Sonido alegre de "nuevo pedido" - melodía ascendente
        const notes = [
            { freq: 523.25, time: 0, duration: 0.15 },      // C5
            { freq: 659.25, time: 0.15, duration: 0.15 },   // E5
            { freq: 783.99, time: 0.3, duration: 0.25 }     // G5
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
        }, 450);
    }

    playStatusChangeSound() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        const ctx = this.audioContext;
        const now = ctx.currentTime;

        // Sonido suave de "actualización" - dos tonos armoniosos
        const notes = [
            { freq: 440, time: 0, duration: 0.2 },      // A4
            { freq: 554.37, time: 0.1, duration: 0.3 }  // C#5
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
    }

    // ==============================================
    // NOTIFICACIONES DEL NAVEGADOR
    // ==============================================

    showBrowserNotification(title, body, icon = "🔔") {
        if (!this.notificationsEnabled) return;

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
    }

    // ==============================================
    // NOTIFICACIONES VISUALES EN PÁGINA
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
    // DETECTORES DE CAMBIOS
    // ==============================================

    checkForNewOrders(orders) {
        const currentCount = orders.length;
        
        if (this.lastOrderCount > 0 && currentCount > this.lastOrderCount) {
            const newOrdersCount = currentCount - this.lastOrderCount;
            const newOrder = orders[0]; // El pedido más reciente
            
            // Sonido
            this.playNewOrderSound();
            
            // Notificación del navegador (incluso si está cerrado)
            this.showBrowserNotification(
                "🆕 Nuevo Pedido Recibido",
                `Pedido #${newOrder.id} de ${newOrder.username || 'Cliente'}\nTotal: ${newOrdersCount} nuevo${newOrdersCount > 1 ? 's' : ''} pedido${newOrdersCount > 1 ? 's' : ''}`,
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
        
        this.lastOrderCount = currentCount;
    }

    checkForStatusChanges(orders) {
        orders.forEach(order => {
            const lastStatus = this.lastOrderStates.get(order.id);
            
            if (lastStatus && lastStatus !== order.status) {
                // El estado cambió
                const statusNames = {
                    'pending': '⏳ Pendiente',
                    'preparing': '🍳 Preparando',
                    'ready': '✅ Listo para recoger',
                    'delivered': '🚀 Entregado'
                };
                
                // Sonido
                this.playStatusChangeSound();
                
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
            
            this.lastOrderStates.set(order.id, order.status);
        });
    }

    // Método para inicializar estados sin notificar
    initializeStates(orders) {
        this.lastOrderCount = orders.length;
        orders.forEach(order => {
            this.lastOrderStates.set(order.id, order.status);
        });
    }
}

// Crear instancia global
window.notificationSystem = new NotificationSystem();