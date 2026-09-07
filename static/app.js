/**
 * ==========================================================================
 * SPEC IDE CLIENT SIDE - VANILLA JS CORE
 * ==========================================================================
 */

// Estado Global de la Aplicación
const state = {
    apiKey: localStorage.getItem('gemini_api_key') || '',
    fallbackApiKey: localStorage.getItem('gemini_fallback_key') || '',
    selectedModel: localStorage.getItem('gemini_model') || 'gemini-2.5-flash',
    lastFailedAction: null,
    isRetryingFromModal: false,
    currentProject: {
        id: '',
        name: 'Sin título',
        seedIdea: '',
        answers: {},
        metadata: {
            domain: 'No especificado',
            productType: 'SaaS',
            actors: [],
            features: []
        }
    },
    activeSpecFile: 'product.md',
    questionTree: [],
    activeQuestionIndex: 0,
    isDarkTheme: false,
    hasBackendApiKey: false,
    generationPath: 'guided',
    dynamicRounds: 0,
    copilotHistory: []
};

// Helper para obtener headers centralizados de IA
function getAiHeaders(customHeaders = {}) {
    return {
        'Content-Type': 'application/json',
        'X-Gemini-Key': state.apiKey || '',
        'X-Gemini-Fallback-Key': state.fallbackApiKey || '',
        'X-Gemini-Model': state.selectedModel || 'gemini-2.5-flash',
        ...customHeaders
    };
}

// Abrir Modal de Cuota Excedida y Fallback de IA
function openQuotaModal(errorDetails = '', retryCallback = null) {
    if (retryCallback) state.lastFailedAction = retryCallback;
    const modal = document.getElementById('ai-quota-modal');
    const detailsBox = document.getElementById('quota-error-details-box');
    const primaryInput = document.getElementById('quota-primary-key');
    const fallbackInput = document.getElementById('quota-fallback-key');
    const modelSelect = document.getElementById('quota-model-select');

    if (detailsBox) detailsBox.innerText = errorDetails || "⚠️ Límite de cuota o Rate Limit (429) alcanzado.";
    if (primaryInput) primaryInput.value = state.apiKey || '';
    if (fallbackInput) fallbackInput.value = state.fallbackApiKey || '';
    if (modelSelect) modelSelect.value = state.selectedModel || 'gemini-2.5-flash';

    if (modal) modal.classList.remove('hidden');
}

// Verificar si la respuesta fue un error de cuota (429/403)
async function checkResponseForQuotaError(response, retryCallback = null) {
    if (response.status === 429 || response.status === 403) {
        let errData = {};
        try { errData = await response.json(); } catch(e) {}
        const errMsg = errData.detail || errData.message || `Error ${response.status}: Límite de Cuota o Rate Limit Excedido.`;
        
        if (state.isRetryingFromModal) {
            showToast(`⚠️ ${errMsg}`, "warning");
            state.isRetryingFromModal = false;
        } else {
            openQuotaModal(errMsg, retryCallback);
        }
        return true;
    }
    return false;
}

// Estructura fija de los 16 archivos de la spec
const SPEC_FILES = [
    { name: 'project.md', label: 'Ficha Técnica', icon: 'fa-file-signature', status: 'pending' },
    { name: 'product.md', label: 'Producto & Valor', icon: 'fa-lightbulb', status: 'pending' },
    { name: 'requirements.md', label: 'Requisitos', icon: 'fa-list-check', status: 'pending' },
    { name: 'user-stories.md', label: 'Historias de Usuario', icon: 'fa-book-open-reader', status: 'pending' },
    { name: 'architecture.md', label: 'Arquitectura', icon: 'fa-sitemap', status: 'pending' },
    { name: 'database.md', label: 'Modelo de Datos', icon: 'fa-database', status: 'pending' },
    { name: 'api.md', label: 'Contrato API (MD)', icon: 'fa-gears', status: 'pending' },
    { name: 'openapi.json', label: 'OpenAPI Spec (JSON)', icon: 'fa-code', status: 'pending' },
    { name: 'frontend.md', label: 'Especificación UI', icon: 'fa-window-maximize', status: 'pending' },
    { name: 'backend.md', label: 'Lógica Backend', icon: 'fa-server', status: 'pending' },
    { name: 'security.md', label: 'Seguridad & Roles', icon: 'fa-user-shield', status: 'pending' },
    { name: 'integrations.md', label: 'Integraciones', icon: 'fa-puzzle-piece', status: 'pending' },
    { name: 'roadmap.md', label: 'Roadmap & MVP', icon: 'fa-map-location-dot', status: 'pending' },
    { name: 'tasks.md', label: 'Lista de Tareas', icon: 'fa-clipboard-list', status: 'pending' },
    { name: 'decisions.md', label: 'Decisiones (ADR)', icon: 'fa-gavel', status: 'pending' },
    { name: 'glossary.md', label: 'Glosario', icon: 'fa-spell-check', status: 'pending' },
    { name: 'agents.md', label: 'Instrucciones IA', icon: 'fa-robot', status: 'pending' }
];

// Documentación detallada de los 17 archivos de especificación para el Onboarding
const SPEC_DOCS = {
    'project.md': {
        title: 'Ficha Técnica del Proyecto',
        category: 'vision',
        categoryLabel: 'Visión & Producto',
        icon: 'fa-file-signature',
        desc: 'Ficha ejecutiva con la idea inicial, resumen conceptual y metadatos generales del proyecto.',
        details: 'Define la semilla del proyecto, su dominio de industria, tipo de producto (SaaS, Mobile, Web), lista de actores detectados e información general del negocio.',
        consumer: 'Humano / IA'
    },
    'product.md': {
        title: 'Producto & Valor',
        category: 'vision',
        categoryLabel: 'Visión & Producto',
        icon: 'fa-lightbulb',
        desc: 'Visión estratégica del producto, propuesta de valor, usuarios/actores y reglas de negocio inquebrantables.',
        details: 'Establece los objetivos de negocio, las métricas de éxito, la descripción de roles de usuario y las reglas lógicas críticas que el código NUNCA puede violar.',
        consumer: 'Agente IA (Dev Prompt & SSOT)'
    },
    'requirements.md': {
        title: 'Requisitos Funcionales y RNF',
        category: 'vision',
        categoryLabel: 'Visión & Producto',
        icon: 'fa-list-check',
        desc: 'Requisitos funcionales (RF) de dominio y requisitos no funcionales (RNF: rendimiento, latencia, seguridad).',
        details: 'Lista numerada de comportamientos esperados del sistema (RF-01, RF-02...) y restricciones técnicas de calidad (RNF-01, RNF-02...).',
        consumer: 'Agente IA / Desarrollador'
    },
    'user-stories.md': {
        title: 'Historias de Usuario & Criterios BDD',
        category: 'vision',
        categoryLabel: 'Visión & Producto',
        icon: 'fa-book-open-reader',
        desc: 'Historias de usuario con criterios de aceptación ejecutables en formato Given/When/Then.',
        details: 'Historias de usuario en formato estándar (Como X, quiero Y, para Z) acompañadas de escenarios de prueba BDD para testing automatizado.',
        consumer: 'Agente IA (TDD / BDD Testing)'
    },
    'architecture.md': {
        title: 'Arquitectura del Sistema',
        category: 'architecture',
        categoryLabel: 'Arquitectura & Datos',
        icon: 'fa-sitemap',
        desc: 'Pila tecnológica propuesta, estructura modular, patrones de diseño y flujo de datos del sistema.',
        details: 'Justificación del tech stack (Frontend, Backend, DB), estructura de directorios recomendada, componentes principales y diagrama de flujo Mermaid.',
        consumer: 'Agente IA (Software Architect)'
    },
    'database.md': {
        title: 'Modelo de Datos & Prisma DSL',
        category: 'architecture',
        categoryLabel: 'Arquitectura & Datos',
        icon: 'fa-database',
        desc: 'Modelo conceptual de entidades, relaciones y el esquema físico completo en sintaxis Prisma DSL / SQL.',
        details: 'Contiene el diagrama ER Mermaid, definición de entidades/atributos y el código schema.prisma completo listo para copiar o migrar.',
        consumer: 'Agente IA (Database Engine)'
    },
    'api.md': {
        title: 'Contrato de API (MD)',
        category: 'architecture',
        categoryLabel: 'Arquitectura & Datos',
        icon: 'fa-gears',
        desc: 'Especificación humana y legible de los endpoints RESTful, rutas, verbos HTTP, payloads y respuestas.',
        details: 'Detalla cada ruta de la API (GET /api/v1/..., POST ...), parámetros requeridos, códigos de respuesta HTTP y contratos JSON de entrada y salida.',
        consumer: 'Humano / Agente IA'
    },
    'openapi.json': {
        title: 'OpenAPI 3.0 Spec (JSON)',
        category: 'architecture',
        categoryLabel: 'Arquitectura & Datos',
        icon: 'fa-code',
        desc: 'Especificación estándar OpenAPI 3.0 en formato JSON estricto para autogenerar clientes, mocks y controladores.',
        details: 'Documento JSON estricto compatible con Swagger, Postman, OpenAPI Generator y herramientas de integración de código automatizado.',
        consumer: 'Swagger / Postman / Codegen'
    },
    'frontend.md': {
        title: 'Especificación UI / UX',
        category: 'ui',
        categoryLabel: 'UI & Lógica',
        icon: 'fa-window-maximize',
        desc: 'Diseño de pantallas, flujo de navegación, componentes UI, estados visuales y guía de estilos.',
        details: 'Fichas de cada pantalla de la app, layout responsive, sistema de componentes reutilizables, paleta de colores HSL y comportamientos visuales.',
        consumer: 'Agente IA (Frontend Dev)'
    },
    'backend.md': {
        title: 'Lógica Backend & Servicios',
        category: 'ui',
        categoryLabel: 'UI & Lógica',
        icon: 'fa-server',
        desc: 'Arquitectura de controladores, capas de servicio, casos de uso, middlewares y validaciones del servidor.',
        details: 'Define la separación en capas (Controller -> Service -> Repository), manejo centralizado de excepciones y reglas de negocio del servidor.',
        consumer: 'Agente IA (Backend Dev)'
    },
    'security.md': {
        title: 'Seguridad, Roles & Permisos',
        category: 'ui',
        categoryLabel: 'UI & Lógica',
        icon: 'fa-user-shield',
        desc: 'Políticas de autenticación (JWT/OAuth), matriz de RBAC (roles y permisos), cifrado y saneamiento.',
        details: 'Detalla cómo se protegen las rutas de la aplicación, manejo de tokens JWT/Cookies HTTP-only, matriz de permisos por rol y saneamiento de entradas.',
        consumer: 'Agente IA (Security Engine)'
    },
    'integrations.md': {
        title: 'Integraciones Externas',
        category: 'ui',
        categoryLabel: 'UI & Lógica',
        icon: 'fa-puzzle-piece',
        desc: 'Configuración de servicios de terceros (Mercado Pago, pasarelas, emails, webhooks, APIs externas).',
        details: 'Especifica la integración con SDKs externos, manejo de webhooks entrantes, flujo de pagos, credenciales de entorno y resiliencia.',
        consumer: 'Agente IA (Integraciones)'
    },
    'roadmap.md': {
        title: 'Roadmap & Alcance MVP',
        category: 'management',
        categoryLabel: 'Gestión & Entrega',
        icon: 'fa-map-location-dot',
        desc: 'Planificación de releases por fases (MVP, Fase 2, Mejoras futuras) marcando el alcance prioritario.',
        details: 'Matriz de priorización MoSCoW (Must, Should, Could, Won\'t) clasificando qué funcionalidades entran en la versión 1.0 vs fases posteriores.',
        consumer: 'Product Manager / Humano'
    },
    'tasks.md': {
        title: 'Lista de Tareas de Código',
        category: 'management',
        categoryLabel: 'Gestión & Entrega',
        icon: 'fa-clipboard-list',
        desc: 'Lista ordenada de tareas técnicas de codificación ejecutables paso a paso por la IA.',
        details: 'Lista de verificación en formato Markdown ([ ] / [x]) dividida por módulos (Setup, Database, Backend, Frontend) para guiar la construcción.',
        consumer: 'Agente IA (Task Execution)'
    },
    'decisions.md': {
        title: 'Registro de Decisiones (ADR)',
        category: 'management',
        categoryLabel: 'Gestión & Entrega',
        icon: 'fa-gavel',
        desc: 'Registro de Decisiones de Arquitectura (ADR) con el contexto y justificación de cada elección técnica.',
        details: 'Documentos ADR (Architecture Decision Records) estructurados con Estado, Contexto, Decisión y Consecuencias para mantener coherencia.',
        consumer: 'Humano / Agente IA'
    },
    'glossary.md': {
        title: 'Glosario & Nomenclatura',
        category: 'management',
        categoryLabel: 'Gestión & Entrega',
        icon: 'fa-spell-check',
        desc: 'Glosario del dominio y mapeo de nombres Español ↔ Inglés para código y base de datos.',
        details: 'Tabla de traducción de conceptos de negocio a identificadores técnicos sugeridos en inglés (ej: Turno -> Appointment, Profesional -> Specialist).',
        consumer: 'Agente IA (Nomenclatura)'
    },
    'agents.md': {
        title: 'Prompt Maestro e Instrucciones IA',
        category: 'management',
        categoryLabel: 'Instrucciones IA',
        icon: 'fa-robot',
        desc: 'Archivo de instrucciones primarias para OpenCode, Cursor o Cline con reglas de estilo y referencia SSOT.',
        details: 'Instrucciones ejecutivas directas que debes copiar/pegar o adjuntar al iniciar tu asistente de código (Cursor, OpenCode, Cline) para que siga la spec.',
        consumer: 'Agente IA (Prompt Inicial)'
    }
};

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// Inicialización de la Aplicación
async function initApp() {
    loadSettings();
    setupTheme();
    setupEventListeners();
    
    // Verificar si el backend tiene la API Key de Gemini configurada
    await checkBackendConfig();
    
    // Cargar la ruta del proyecto activo en la interfaz
    await checkProjectPath();

    // Intentar cargar proyecto existente del backend (para mostrar en Dashboard)
    await checkExistingProject();
}

// Actualizar la etiqueta visual del modelo seleccionado en la barra superior
function updateHeaderModelLabel(modelId) {
    const textSpan = document.getElementById('header-selected-model-text');
    const menuItems = document.querySelectorAll('.model-menu-item');
    
    const labels = {
        'gemini-2.5-flash': '⚡ 2.5 Flash',
        'gemini-3.1-pro-preview': '🧠 3.1 Pro',
        'gemini-2.0-flash': '⚡ 2.0 Flash',
        'gemini-flash-latest': '⚡ Flash Latest',
        'deepseek-chat': '🐳 DeepSeek V3',
        'deepseek-reasoner': '🐳 DeepSeek R1'
    };
    
    if (textSpan) {
        textSpan.innerText = labels[modelId] || modelId;
    }
    
    menuItems.forEach(item => {
        if (item.getAttribute('data-value') === modelId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Cargar configuraciones del almacenamiento local
function loadSettings() {
    state.apiKey = localStorage.getItem('gemini_api_key') || '';
    state.fallbackApiKey = localStorage.getItem('gemini_fallback_key') || '';
    let savedModel = localStorage.getItem('gemini_model') || 'gemini-2.5-flash';
    if (savedModel === 'gemini-2.5-pro' || savedModel === 'gemini-1.5-pro') savedModel = 'gemini-3.1-pro-preview';
    if (savedModel === 'gemini-1.5-flash') savedModel = 'gemini-2.5-flash';
    state.selectedModel = savedModel;
    
    const keyInput = document.getElementById('gemini-api-key');
    if (keyInput) keyInput.value = state.apiKey;

    updateHeaderModelLabel(state.selectedModel);
    
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        state.isDarkTheme = true;
    } else if (theme === 'light') {
        state.isDarkTheme = false;
    }
}

// Verificar la ruta activa del proyecto en el servidor
async function checkProjectPath() {
    try {
        const response = await fetch('/api/project-path');
        const data = await response.json();
        if (data.status === 'success' && data.project_path) {
            const input = document.getElementById('project-target-path-input');
            if (input && !input.value) {
                input.value = data.project_path;
            }
        }
    } catch (e) {
        console.error("Error obteniendo la ruta del proyecto:", e);
    }
}

// Actualizar indicador visual del estado de la clave API
function updateKeyStatusUI() {
    const keyInput = document.getElementById('gemini-api-key');
    const keyIcon = document.getElementById('key-status-icon');
    if (!keyInput) return;

    if (state.apiKey) {
        keyInput.value = state.apiKey;
        keyInput.placeholder = "Clave personalizada activa";
        if (keyIcon) {
            keyIcon.style.color = "var(--success)";
            keyIcon.title = "Clave API personalizada guardada en el navegador";
        }
    } else if (state.hasBackendApiKey) {
        keyInput.value = "";
        keyInput.placeholder = "Configurada en servidor (.env)";
        if (keyIcon) {
            keyIcon.style.color = "var(--accent)";
            keyIcon.title = "Clave API configurada en archivo .env del servidor";
        }
    } else {
        keyInput.value = "";
        keyInput.placeholder = "Gemini API Key...";
        if (keyIcon) {
            keyIcon.style.color = "var(--text-muted)";
            keyIcon.title = "Sin clave API configurada";
        }
    }
}

// Verificar si el servidor ya tiene la API Key configurada
async function checkBackendConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        state.hasBackendApiKey = data.hasApiKey;
        if (data.hasFallbackKey) {
            state.hasBackendFallbackKey = true;
        }
        updateKeyStatusUI();
    } catch (e) {
        console.error("Error al obtener la configuración del backend:", e);
    }
}

// Configurar el tema visual
function setupTheme() {
    const body = document.body;
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (state.isDarkTheme) {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    } else {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }
}

// Comprobar si hay un proyecto activo y obtener la lista de recientes
async function checkExistingProject() {
    try {
        const [activeResp, recentResp] = await Promise.all([
            fetch('/api/load-project'),
            fetch('/api/recent-projects')
        ]);
        
        const activeData = await activeResp.json();
        const recentData = await recentResp.json();

        if (activeData.status === 'success' && activeData.project) {
            state.currentProject = activeData.project;
        }

        const projectsList = (recentData.status === 'success' && recentData.projects) ? recentData.projects : [];
        renderRecentProjectsList(projectsList);
    } catch (e) {
        console.error("Error cargando proyecto y recientes:", e);
        renderRecentProjectsList([]);
    }
}

// Mostrar listado de proyectos recientes en el Dashboard
function renderRecentProjectsList(projects) {
    const container = document.getElementById('recent-projects-list');
    if (!container) return;

    if (!projects || projects.length === 0) {
        container.innerHTML = `
            <div class="empty-projects-state">
                <i class="fa-solid fa-diagram-project"></i>
                <p>No hay proyectos activos cargados. <br>Inicia uno nuevo para comenzar.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = projects.map(proj => {
        const dateStr = new Date(proj.updatedAt || Date.now()).toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        const activeBadge = proj.isActive 
            ? `<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); font-size: 10px; padding: 2px 6px;">Activo</span>`
            : '';

        return `
            <div class="recent-project-item ${proj.isActive ? 'active-project-card' : ''}" data-path="${proj.path}">
                <div class="project-item-info">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="project-item-title">${proj.name}</span>
                        ${activeBadge}
                    </div>
                    <span class="project-item-date">Modificado: ${dateStr} &bull; <span style="font-family: monospace; font-size: 10px; color: var(--text-muted);">${proj.path}</span></span>
                </div>
                <div class="project-item-action">
                    <i class="fa-solid fa-chevron-right"></i>
                </div>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.recent-project-item').forEach(item => {
        item.addEventListener('click', async () => {
            const targetPath = item.getAttribute('data-path');
            if (targetPath) {
                try {
                    await fetch('/api/set-project-path', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ project_path: targetPath })
                    });
                    
                    const loadResp = await fetch('/api/load-project');
                    const loadData = await loadResp.json();
                    if (loadData.status === 'success' && loadData.project) {
                        state.currentProject = loadData.project;
                    }
                    showToast(`Cargando proyecto "${state.currentProject.name}"`, "info");
                    loadWorkspace();
                } catch (err) {
                    console.error("Error cambiando a proyecto:", err);
                    showToast("No se pudo cargar el proyecto seleccionado.", "error");
                }
            }
        });
    });
}

// Configurar los manejadores de eventos
function setupEventListeners() {
    // Alternar Tema
    document.getElementById('theme-toggle-btn').addEventListener('click', () => {
        state.isDarkTheme = !state.isDarkTheme;
        localStorage.setItem('theme', state.isDarkTheme ? 'dark' : 'light');
        setupTheme();
    });

    // Guardar o borrar API Key de Gemini
    const saveKeyAction = () => {
        const keyInput = document.getElementById('gemini-api-key');
        if (!keyInput) return;
        const key = keyInput.value.trim();
        if (key) {
            state.apiKey = key;
            localStorage.setItem('gemini_api_key', key);
            showToast("Clave API personalizada guardada", "success");
        } else {
            state.apiKey = '';
            localStorage.removeItem('gemini_api_key');
            if (state.hasBackendApiKey) {
                showToast("Usando la clave API del archivo .env del servidor", "info");
            } else {
                showToast("Campo vacío: No hay clave API local guardada", "warning");
            }
        }
        updateKeyStatusUI();
    };

    document.getElementById('save-api-key-btn').addEventListener('click', saveKeyAction);
    document.getElementById('gemini-api-key').addEventListener('change', saveKeyAction);
    document.getElementById('btn-open-keys-modal')?.addEventListener('click', () => openQuotaModal('Configuración de Claves de IA (Principal y Resguardo)'));

    // Selección de Plantilla Presets
    const chips = document.querySelectorAll('.preset-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        });
    });

    // Selección de Metodología (Camino 1 vs Camino 2)
    const pathOptions = document.querySelectorAll('.path-option');
    pathOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            pathOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            state.generationPath = opt.dataset.path;
            
            const startBtnText = document.querySelector('#start-discovery-btn span');
            if (state.generationPath === 'direct') {
                startBtnText.innerText = "Generar Specs Directamente";
            } else {
                startBtnText.innerText = "Iniciar Descubrimiento con Gemini";
            }
        });
    });

    // Iniciar Descubrimiento
    document.getElementById('start-discovery-btn').addEventListener('click', () => {
        startDiscoveryFlow();
    });

    // Navegación: Volver al Dashboard desde Logo y Botón de Inicio
    const headerLogo = document.getElementById('btn-header-logo');
    if (headerLogo) {
        headerLogo.addEventListener('click', () => showScreen('screen-dashboard'));
    }

    const switchProjBtn = document.getElementById('btn-switch-project');
    if (switchProjBtn) {
        switchProjBtn.addEventListener('click', () => showScreen('screen-dashboard'));
    }

    // Volver al Inicio desde el Wizard
    document.getElementById('back-to-dashboard-btn').addEventListener('click', () => {
        showScreen('screen-dashboard');
    });

    // Saltarse la entrevista
    document.getElementById('skip-to-workspace-btn').addEventListener('click', () => {
        loadWorkspace();
    });

    // Wizard: Siguiente y Anterior
    document.getElementById('wizard-next-btn').addEventListener('click', handleWizardNext);
    document.getElementById('wizard-prev-btn').addEventListener('click', handleWizardPrev);
    document.getElementById('wizard-finish-btn').addEventListener('click', finishInterviewAndGenerateSpecs);

    // Exportar Specs
    document.getElementById('btn-export-specs').addEventListener('click', exportSpecsToDisk);

    // Modal de Onboarding / Guía de Specs
    const onboardingModal = document.getElementById('onboarding-modal');
    const openOnboardingBtn = document.getElementById('btn-open-onboarding');
    const bannerMoreInfoBtn = document.getElementById('btn-banner-more-info');
    const closeOnboardingBtn = document.getElementById('btn-close-onboarding-modal');

    const openOnboardingHandler = () => {
        renderOnboardingGrid('all');
        if (onboardingModal) onboardingModal.classList.remove('hidden');
    };

    if (openOnboardingBtn) openOnboardingBtn.addEventListener('click', openOnboardingHandler);
    if (bannerMoreInfoBtn) bannerMoreInfoBtn.addEventListener('click', openOnboardingHandler);
    if (closeOnboardingBtn) {
        closeOnboardingBtn.addEventListener('click', () => {
            if (onboardingModal) onboardingModal.classList.add('hidden');
        });
    }

    if (onboardingModal) {
        onboardingModal.addEventListener('click', (e) => {
            if (e.target === onboardingModal) {
                onboardingModal.classList.add('hidden');
            }
        });
    }

    // Pestañas de categorías del Onboarding
    const tabBtns = document.querySelectorAll('.onboarding-tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const targetCategory = btn.dataset.category || btn.dataset.tab || 'all';
            renderOnboardingGrid(targetCategory);
        });
    });

    // Spec Copilot Event Listeners
    const toggleCopilotBtn = document.getElementById('btn-toggle-copilot');
    const closeCopilotBtn = document.getElementById('btn-close-copilot');
    const expandCopilotBtn = document.getElementById('btn-expand-copilot');
    const clearCopilotBtn = document.getElementById('btn-clear-copilot');
    const sendCopilotBtn = document.getElementById('btn-send-copilot');
    const copilotInput = document.getElementById('copilot-input');
    const exploreFinishWizardBtn = document.getElementById('btn-explore-finish-wizard');

    if (toggleCopilotBtn) toggleCopilotBtn.addEventListener('click', toggleCopilotPanel);
    if (closeCopilotBtn) closeCopilotBtn.addEventListener('click', toggleCopilotPanel);
    if (clearCopilotBtn) clearCopilotBtn.addEventListener('click', clearCopilotChat);
    if (sendCopilotBtn) sendCopilotBtn.addEventListener('click', () => sendCopilotMessage());
    if (exploreFinishWizardBtn) exploreFinishWizardBtn.addEventListener('click', extractAnswersAndLaunchWizard);

    // Event Listeners del Selector de Modelo de IA Personalizado (Dropdown UI)
    const triggerBtn = document.getElementById('btn-custom-model-trigger');
    const modelMenu = document.getElementById('custom-model-menu');
    const menuItems = document.querySelectorAll('.model-menu-item');

    if (triggerBtn && modelMenu) {
        triggerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            modelMenu.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!modelMenu.contains(e.target) && !triggerBtn.contains(e.target)) {
                modelMenu.classList.add('hidden');
            }
        });

        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const val = item.getAttribute('data-value');
                state.selectedModel = val;
                localStorage.setItem('gemini_model', val);
                
                updateHeaderModelLabel(val);
                const quotaSelect = document.getElementById('quota-model-select');
                if (quotaSelect) quotaSelect.value = val;
                
                modelMenu.classList.add('hidden');
                showToast(`Modelo de IA cambiado a: ${item.innerText}`, "info");
            });
        });
    }

    const saveQuotaBtn = document.getElementById('btn-save-quota-modal');
    const closeQuotaBtn = document.getElementById('btn-close-quota-modal');
    const quotaModal = document.getElementById('ai-quota-modal');

    if (closeQuotaBtn) {
        closeQuotaBtn.addEventListener('click', () => {
            if (quotaModal) quotaModal.classList.add('hidden');
        });
    }

    if (quotaModal) {
        quotaModal.addEventListener('click', (e) => {
            if (e.target === quotaModal) quotaModal.classList.add('hidden');
        });
    }

    if (saveQuotaBtn) {
        saveQuotaBtn.addEventListener('click', async () => {
            const primaryKey = document.getElementById('quota-primary-key').value.trim();
            const fallbackKey = document.getElementById('quota-fallback-key').value.trim();
            const modelVal = document.getElementById('quota-model-select').value;

            state.apiKey = primaryKey;
            state.fallbackApiKey = fallbackKey;
            state.selectedModel = modelVal;

            localStorage.setItem('gemini_api_key', primaryKey);
            localStorage.setItem('gemini_fallback_key', fallbackKey);
            localStorage.setItem('gemini_model', modelVal);

            updateKeyStatusUI();
            updateHeaderModelLabel(modelVal);

            if (quotaModal) quotaModal.classList.add('hidden');
            showToast("Configuración de IA guardada exitosamente", "success");

            if (typeof state.lastFailedAction === 'function') {
                const retryFn = state.lastFailedAction;
                state.lastFailedAction = null;
                state.isRetryingFromModal = true;
                showToast("Reintentando consulta...", "info");
                try {
                    await retryFn();
                } catch(err) {
                    console.error("Error al reintentar la consulta:", err);
                } finally {
                    state.isRetryingFromModal = false;
                }
            }
        });
    }

    if (expandCopilotBtn) {
        expandCopilotBtn.addEventListener('click', () => {
            const panel = document.getElementById('workspace-copilot-panel');
            if (panel) {
                panel.classList.toggle('expanded');
                const isExp = panel.classList.contains('expanded');
                expandCopilotBtn.innerHTML = isExp ? '<i class="fa-solid fa-compress"></i>' : '<i class="fa-solid fa-expand"></i>';
                expandCopilotBtn.title = isExp ? 'Restaurar vista lateral del chat' : 'Expandir chat a pantalla completa / modo amplio';
            }
        });
    }

    if (copilotInput) {
        copilotInput.addEventListener('input', () => {
            copilotInput.style.height = 'auto';
            copilotInput.style.height = Math.min(copilotInput.scrollHeight, 140) + 'px';
        });

        copilotInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendCopilotMessage();
            }
        });
    }

    document.querySelectorAll('.copilot-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            if (query) sendCopilotMessage(query);
        });
    });

    // Modal de Planificación de Features
    const planningModal = document.getElementById('planning-modal');
    
    document.getElementById('btn-open-planning').addEventListener('click', () => {
        showPlanningState('initial');
        const customInput = document.getElementById('planning-custom-input');
        if (customInput) customInput.value = '';
        planningModal.classList.remove('hidden');
    });
    
    document.getElementById('btn-close-planning-modal').addEventListener('click', () => {
        planningModal.classList.add('hidden');
    });
    
    document.getElementById('planning-modal-overlay').addEventListener('click', () => {
        planningModal.classList.add('hidden');
    });
    
    document.getElementById('btn-cancel-generation').addEventListener('click', () => {
        planningModal.classList.add('hidden');
    });
    
    document.getElementById('btn-start-planning-analysis').addEventListener('click', runPlanningAnalysis);
    document.getElementById('btn-submit-generation').addEventListener('click', submitFeatureGeneration);

    // Abrir la carpeta de especificaciones local en el editor
    document.getElementById('btn-open-in-editor').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/open-specs-folder', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast(data.message, "success");
            } else {
                throw new Error("No se pudo abrir la carpeta");
            }
        } catch (e) {
            console.error(e);
            showToast("Error al abrir la carpeta de especificaciones", "error");
        }
    });

    // Completar con IA en el editor
    document.getElementById('btn-ai-autocomplete').addEventListener('click', autocompleteActiveSection);

    // Copiar Prompt para Agente Dev (Open Code, Cursor, Cline, etc)
    document.getElementById('btn-copy-agent-prompt').addEventListener('click', () => copyAgentPrompt());

    // Selector de carpeta destino nativa
    const selectFolderBtn = document.getElementById('btn-select-folder-dialog');
    if (selectFolderBtn) {
        selectFolderBtn.addEventListener('click', async () => {
            try {
                showToast("Abriendo explorador de carpetas del sistema...", "info");
                const response = await fetch('/api/select-folder-dialog', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'success' && data.selected_path) {
                    document.getElementById('project-target-path-input').value = data.selected_path;
                    showToast(`Carpeta seleccionada: ${data.selected_path}`, "success");
                } else if (data.status === 'cancelled') {
                    showToast(data.message || "Selección de carpeta cancelada.", "info");
                } else if (data.status === 'manual_required') {
                    showToast(data.message, "info");
                }
            } catch (e) {
                console.error("Error al abrir diálogo de carpeta:", e);
                showToast("Ingresa la ruta manualmente en el campo de texto.", "info");
            }
        });
    }
}

// Alternar pantallas del SPA
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
    
    // Ocultar o mostrar barra superior e indicador de progreso según pantalla
    const headerIndicator = document.getElementById('project-indicator');
    const globalProgress = document.getElementById('global-progress-bar');
    
    if (screenId === 'screen-workspace') {
        headerIndicator.classList.remove('hidden');
        globalProgress.classList.remove('hidden');
        document.getElementById('current-project-name').innerText = state.currentProject.name;
        updateGlobalProgressBar();
    } else {
        headerIndicator.classList.add('hidden');
        globalProgress.classList.add('hidden');
    }
}

// Actualizar barra de completitud global
function updateGlobalProgressBar() {
    const total = SPEC_FILES.length;
    let completed = 0;
    
    SPEC_FILES.forEach(file => {
        const nameKey = file.name.replace('.md', '').replace('.json', '');
        const hasContent = state.currentProject && state.currentProject.specModules && state.currentProject.specModules[nameKey] && state.currentProject.specModules[nameKey].trim().length > 0;
        if (hasContent) {
            file.status = 'completed';
            completed++;
        } else {
            file.status = 'pending';
        }
    });
    
    const percentage = Math.round((completed / total) * 100);
    const percentEl = document.getElementById('progress-percent');
    const fillEl = document.getElementById('progress-fill-bar');
    if (percentEl) percentEl.innerText = `${percentage}%`;
    if (fillEl) fillEl.style.width = `${percentage}%`;
    
    renderSpecTree();
}

// Iniciar el flujo de descubrimiento
async function startDiscoveryFlow() {
    const name = document.getElementById('project-name-input').value.trim();
    const seedIdea = document.getElementById('project-seed-idea').value.trim();
    
    if (!name || !seedIdea) {
        showToast("Por favor, ingresa el nombre de tu proyecto y la idea semilla", "error");
        return;
    }
    
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Es necesario ingresar una API Key de Gemini en el Header o configurarla en el servidor", "error");
        return;
    }

    // Configurar carpeta destino (o crear subcarpeta dedicada basada en el slug del nombre)
    const targetPathInput = document.getElementById('project-target-path-input');
    let targetPath = targetPathInput ? targetPathInput.value.trim() : '';

    if (!targetPath) {
        const slug = name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || 'nuevo-proyecto';
        targetPath = `./projects/${slug}`;
    }

    try {
        const setResp = await fetch('/api/set-project-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_path: targetPath })
        });
        const setJson = await setResp.json();
        if (setJson.status === 'success') {
            console.log(`Carpeta del proyecto configurada en: ${setJson.project_path}`);
        }
    } catch (setErr) {
        console.error("Error configurando ruta destino:", setErr);
    }
    
    // Inicializar estado del proyecto
    state.currentProject = {
        id: 'proj_' + Math.random().toString(36).substr(2, 9),
        name: name,
        seedIdea: seedIdea,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        answers: {},
        specModules: {},
        metadata: { domain: 'Descubriendo...', productType: 'Web', actors: [], features: [] }
    };
    
    await saveProjectToServer();
    
    if (state.generationPath === 'direct') {
        showScreen('screen-discovery');
        document.getElementById('discovery-loader').classList.remove('hidden');
        document.getElementById('wizard-container').classList.add('hidden');
        document.getElementById('loader-status-text').innerText = "Gemini está analizando conceptualmente tu idea...";
        
        try {
            // 1. Obtener metadatos básicos
            const response = await fetch('/api/analyze-idea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': state.apiKey
                },
                body: JSON.stringify({ idea: seedIdea })
            });
            
            const data = await response.json();
            state.currentProject.metadata.domain = data.domain || 'Por definir';
            state.currentProject.metadata.productType = data.productType || 'SaaS';
            state.currentProject.metadata.actors = data.actors || [];
            state.currentProject.metadata.features = data.detectedFeatures || [];
            
            updateConceptualAnalysisPanel();
            
            // 2. Generar directamente las especificaciones con la IA
            document.getElementById('loader-status-text').innerText = "Generando especificaciones en formato Markdown...";
            
            await saveProjectToServer();
            startPollingGenerationStatus();
            
            try {
                const exportResponse = await fetch('/api/export-specs', {
                    method: 'POST',
                    headers: getAiHeaders(),
                    body: JSON.stringify({ project_data: state.currentProject })
                });
                
                const isQuota = await checkResponseForQuotaError(exportResponse, startDiscoveryFlow);
                if (isQuota) {
                    stopPollingGenerationStatus();
                    return;
                }
                
                const exportData = await exportResponse.json();
                stopPollingGenerationStatus();

                if (exportData.status === 'success') {
                    const loadResp = await fetch('/api/load-project');
                    const loadData = await loadResp.json();
                    
                    if (loadData.status === 'success' && loadData.project) {
                        state.currentProject = loadData.project;
                    }
                    showToast("Especificaciones generadas directamente con éxito", "success");
                    loadWorkspace();
                } else {
                    throw new Error(exportData.detail || "La generación de especificaciones no devolvió éxito.");
                }
            } catch (exportErr) {
                stopPollingGenerationStatus();
                throw exportErr;
            }
        } catch (e) {
            console.error(e);
            showToast("Error en la generación directa. Redirigiendo a pantalla de inicio.", "error");
            showScreen('screen-dashboard');
        }
    } else {
        // Modo 1: Explore Chat + Wizard Inteligente
        showToast("Modo Explore activado. Habla con Spec Copilot para definir tu producto.", "info");

        // Limpiar o reiniciar chat para el nuevo proyecto
        state.copilotHistory = [];
        try {
            await fetch('/api/copilot-clear-history', { method: 'POST' });
        } catch (e) {}

        // Abrir Workspace con Copilot desplegado
        loadWorkspace();

        const copilotPanel = document.getElementById('workspace-copilot-panel');
        if (copilotPanel) {
            copilotPanel.classList.remove('hidden');
            copilotPanel.classList.add('expanded');
        }

        const exploreBtn = document.getElementById('btn-explore-finish-wizard');
        if (exploreBtn) exploreBtn.classList.remove('hidden');

        // Mensaje de bienvenida de Spec Copilot en Explore
        const welcomeMsg = `¡Hola! He registrado la idea inicial para **${name}**:\n> *"${seedIdea}"*\n\nPodemos charlar libremente sobre las funcionalidades que imaginas, los usuarios principales, reglas de negocio o tecnología.\n\nCuando estés listo para generar las especificaciones, haz clic en el botón verde arriba a la derecha: **📋 Revisar Cuestionario & Redactar Specs**.`;

        state.copilotHistory = [
            { role: 'model', content: welcomeMsg }
        ];

        try {
            await fetch('/api/copilot-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': state.apiKey || ''
                },
                body: JSON.stringify({
                    message: "__init_explore__",
                    history: state.copilotHistory,
                    project_data: state.currentProject
                })
            });
        } catch (e) {}

        const container = document.getElementById('copilot-messages');
        if (container) {
            container.innerHTML = '';
            appendCopilotMsg('ai', welcomeMsg, true);
        }
    }
}

// Extraer respuestas de la charla de Explore y abrir el Wizard pre-llenado
async function extractAnswersAndLaunchWizard() {
    showToast("Gemini está analizando la conversación para pre-llenar tu cuestionario...", "info");

    try {
        const extractResp = await fetch('/api/explore-extract-answers', {
            method: 'POST',
            headers: getAiHeaders(),
            body: JSON.stringify({
                history: state.copilotHistory || []
            })
        });

        const isQuota = await checkResponseForQuotaError(extractResp, extractAnswersAndLaunchWizard);
        if (isQuota) return;

        const extractData = await extractResp.json();
        let extractedAnswers = extractData.answers || extractData.extracted_answers || {};

        // Obtener questionTree si no existe
        if (!state.questionTree || state.questionTree.length === 0) {
            try {
                const analyzeResp = await fetch('/api/analyze-idea', {
                    method: 'POST',
                    headers: getAiHeaders(),
                    body: JSON.stringify({ idea: (state.currentProject && state.currentProject.seedIdea) || '' })
                });
                const isAnalyzeQuota = await checkResponseForQuotaError(analyzeResp, extractAnswersAndLaunchWizard);
                if (!isAnalyzeQuota) {
                    const analyzeData = await analyzeResp.json();
                    state.questionTree = analyzeData.questions || [];
                }
            } catch (aErr) {
                console.error("Error al obtener árbol de preguntas:", aErr);
            }
        }

        // Pre-llenar respuestas en el objeto del proyecto
        if (!state.currentProject) state.currentProject = {};
        if (!state.currentProject.answers) state.currentProject.answers = {};

        if (state.questionTree && state.questionTree.length > 0) {
            state.questionTree.forEach(q => {
                const val = extractedAnswers[q.id];
                if (val) {
                    if (q.type === 'select' && q.options) {
                        const matchedOpt = q.options.find(opt => 
                            opt.toLowerCase().includes(val.toLowerCase()) || 
                            val.toLowerCase().includes(opt.toLowerCase())
                        );
                        state.currentProject.answers[q.id] = matchedOpt || val;
                    } else {
                        state.currentProject.answers[q.id] = val;
                    }
                }
            });
        }

        await saveProjectToServer();

        // Transición al Wizard en screen-discovery
        showScreen('screen-discovery');
        document.getElementById('discovery-loader').classList.add('hidden');
        document.getElementById('wizard-container').classList.remove('hidden');

        state.activeQuestionIndex = 0;
        state.dynamicRounds = 0;
        renderWizardQuestion();

        showToast("Cuestionario pre-llenado exitosamente. Revisa tus opciones y haz clic en Finalizar.", "success");

    } catch (err) {
        console.error("Error extrayendo respuestas del Explore Chat:", err);
        showToast("No se pudieron extraer automáticamente las respuestas, pero puedes completarlas manualmente.", "warning");
        showScreen('screen-discovery');
        document.getElementById('discovery-loader').classList.add('hidden');
        document.getElementById('wizard-container').classList.remove('hidden');
        renderWizardQuestion();
    }
}

// Actualizar panel conceptual derecho en el wizard
function updateConceptualAnalysisPanel() {
    const meta = state.currentProject.metadata;
    document.getElementById('meta-domain').innerText = meta.domain;
    document.getElementById('meta-type').innerText = meta.productType;
    
    const actorsContainer = document.getElementById('meta-actors');
    actorsContainer.innerHTML = meta.actors.map(actor => `<span class="meta-chip">${actor}</span>`).join('');
    
    const featuresContainer = document.getElementById('meta-features');
    featuresContainer.innerHTML = meta.features.map(feat => `<li>${feat}</li>`).join('');
}

// Renderizar pregunta en el Wizard
function renderWizardQuestion() {
    if (state.questionTree.length === 0) {
        loadWorkspace();
        return;
    }
    
    const q = state.questionTree[state.activeQuestionIndex];
    const isDynamic = state.dynamicRounds > 0;
    const phaseLabel = isDynamic ? "Fase 2: Refinamiento Técnico de IA" : "Fase 1: Descubrimiento de Negocio";
    document.getElementById('wizard-step-indicator').innerText = `[${phaseLabel}] Pregunta ${state.activeQuestionIndex + 1} de ${state.questionTree.length}`;
    document.getElementById('wizard-progress-fill').style.width = `${((state.activeQuestionIndex + 1) / state.questionTree.length) * 100}%`;
    
    document.getElementById('question-category').innerText = q.section;
    document.getElementById('question-text').innerText = q.label;
    
    const inputContainer = document.getElementById('answer-input-container');
    inputContainer.innerHTML = '';
    
    // Cargar respuesta previa si existe
    const prevAnswer = state.currentProject.answers[q.id] || '';
    
    if (q.type === 'select') {
        const grid = document.createElement('div');
        grid.className = 'select-options-grid';
        
        const optionsList = [...(q.options || [])];
        
        // Incluir opción "Ninguna / Sin autenticación" si es una pregunta sobre seguridad/auth
        const isAuthQuestion = q.id === 'q_auth' || (q.section && q.section.toLowerCase().includes('segurid')) || (q.label && q.label.toLowerCase().includes('autentic'));
        if (isAuthQuestion && !optionsList.some(o => o.toLowerCase().includes('ningun') || o.toLowerCase().includes('sin aut'))) {
            optionsList.unshift("Ninguna / Sin autenticación (API instalada, CLI, herramienta local)");
        }
        
        // Incluir siempre opción personalizada "Otra..."
        const customOptLabel = "Otra (Escribir respuesta personalizada...)";
        if (!optionsList.includes(customOptLabel)) {
            optionsList.push(customOptLabel);
        }

        const customContainer = document.createElement('div');
        customContainer.style.marginTop = '12px';
        customContainer.className = 'hidden';
        
        const customTextarea = document.createElement('textarea');
        customTextarea.placeholder = "Escribe tu respuesta personalizada aquí...";
        customTextarea.value = prevAnswer.startsWith("Otra:") ? prevAnswer.replace("Otra:", "").trim() : "";
        customTextarea.addEventListener('input', (e) => {
            state.currentProject.answers[q.id] = `Otra: ${e.target.value.trim()}`;
        });
        customContainer.appendChild(customTextarea);

        optionsList.forEach(opt => {
            const isCustom = opt === customOptLabel;
            const isSelected = isCustom ? prevAnswer.startsWith("Otra:") : prevAnswer === opt;

            const item = document.createElement('div');
            item.className = `select-option-item ${isSelected ? 'selected' : ''}`;
            item.innerHTML = `<i class="fa-regular ${isSelected ? 'fa-circle-dot' : 'fa-circle'}"></i> <span>${opt}</span>`;
            
            if (isSelected && isCustom) {
                customContainer.classList.remove('hidden');
            }

            item.addEventListener('click', () => {
                grid.querySelectorAll('.select-option-item').forEach(el => el.classList.remove('selected'));
                grid.querySelectorAll('i').forEach(i => {
                    i.className = 'fa-regular fa-circle';
                });
                
                item.classList.add('selected');
                item.querySelector('i').className = 'fa-solid fa-circle-dot';
                
                if (isCustom) {
                    customContainer.classList.remove('hidden');
                    customTextarea.focus();
                    state.currentProject.answers[q.id] = customTextarea.value ? `Otra: ${customTextarea.value.trim()}` : "Otra";
                } else {
                    customContainer.classList.add('hidden');
                    state.currentProject.answers[q.id] = opt;
                }
            });
            grid.appendChild(item);
        });
        
        inputContainer.appendChild(grid);
        inputContainer.appendChild(customContainer);
    } else {
        const textarea = document.createElement('textarea');
        textarea.placeholder = "Escribe tu respuesta aquí de forma clara...";
        textarea.value = prevAnswer;
        textarea.addEventListener('input', (e) => {
            state.currentProject.answers[q.id] = e.target.value;
        });
        inputContainer.appendChild(textarea);
    }
    
    // Activar/desactivar botón anterior
    document.getElementById('wizard-prev-btn').disabled = state.activeQuestionIndex === 0;
}

// Avanzar en el Wizard
async function handleWizardNext() {
    const q = state.questionTree[state.activeQuestionIndex];
    if (!state.currentProject.answers[q.id]) {
        showToast("Por favor, responde la pregunta antes de continuar", "info");
        return;
    }
    
    if (state.activeQuestionIndex < state.questionTree.length - 1) {
        state.activeQuestionIndex++;
        renderWizardQuestion();
    } else {
        // Fin del wizard inicial. Pedimos preguntas técnicas dinámicas extras
        await requestAdditionalQuestions();
    }
}

// Retroceder en el Wizard
function handleWizardPrev() {
    if (state.activeQuestionIndex > 0) {
        state.activeQuestionIndex--;
        renderWizardQuestion();
    }
}

// Solicitar preguntas secundarias a Gemini
async function requestAdditionalQuestions() {
    if ((state.dynamicRounds || 0) >= 1) {
        // Ya completamos la ronda técnica dinámica, terminamos la entrevista y redactamos
        await finishInterviewAndGenerateSpecs();
        return;
    }
    
    state.dynamicRounds = (state.dynamicRounds || 0) + 1;
    
    document.getElementById('discovery-loader').classList.remove('hidden');
    document.getElementById('wizard-container').classList.add('hidden');
    document.getElementById('loader-status-text').innerText = "Generando preguntas técnicas específicas...";
    
    try {
        const response = await fetch('/api/next-questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({
                idea: state.currentProject.seedIdea,
                answers: state.currentProject.answers
            })
        });
        
        const data = await response.json();
        
        if (data.questions && data.questions.length > 0) {
            // Unimos las nuevas preguntas al árbol
            state.questionTree = [...state.questionTree, ...data.questions];
            state.activeQuestionIndex++;
            document.getElementById('discovery-loader').classList.add('hidden');
            document.getElementById('wizard-container').classList.remove('hidden');
            renderWizardQuestion();
        } else {
            // No hay más preguntas, finalizamos y redactamos
            await finishInterviewAndGenerateSpecs();
        }
    } catch (e) {
        console.error(e);
        await finishInterviewAndGenerateSpecs();
    }
}

// Finalizar entrevista guiada y disparar generación completa de specs
async function finishInterviewAndGenerateSpecs() {
    // Si no ha contestado nada, mostramos aviso
    const answeredCount = Object.keys(state.currentProject.answers).length;
    if (answeredCount === 0) {
        showToast("Por favor responde al menos una pregunta para poder generar las especificaciones", "info");
        return;
    }
    
    showScreen('screen-discovery');
    document.getElementById('discovery-loader').classList.remove('hidden');
    document.getElementById('wizard-container').classList.add('hidden');
    document.getElementById('loader-status-text').innerText = "Gemini está redactando todas tus especificaciones a partir de tus respuestas...";
    
    await saveProjectToServer();
    startPollingGenerationStatus();
    
    try {
        const exportResponse = await fetch('/api/export-specs', {
            method: 'POST',
            headers: getAiHeaders(),
            body: JSON.stringify({ project_data: state.currentProject })
        });
        
        const isQuota = await checkResponseForQuotaError(exportResponse, finishInterviewAndGenerateSpecs);
        if (isQuota) {
            stopPollingGenerationStatus();
            return;
        }

        const exportData = await exportResponse.json();
        stopPollingGenerationStatus();

        if (exportData.status === 'success') {
            const loadResp = await fetch('/api/load-project');
            const loadData = await loadResp.json();
            
            if (loadData.status === 'success' && loadData.project) {
                state.currentProject = loadData.project;
            }
            showToast("Especificaciones redactadas con éxito basándose en tu entrevista", "success");
            loadWorkspace();
        } else {
            showToast(exportData.detail || "Hubo un error al generar las especificaciones, ingresando al Workspace.", "error");
            loadWorkspace();
        }
    } catch (e) {
        stopPollingGenerationStatus();
        console.error(e);
        showToast("Error de conexión al redactar especificaciones. Redirigiendo al Workspace.", "error");
        loadWorkspace();
    }
}

// Carga del Workspace IDE
function loadWorkspace() {
    showScreen('screen-workspace');
    selectSpecFile('product.md');
    saveProjectToServer();
    loadCopilotHistory();

    const hasGeneratedSpecs = state.currentProject && state.currentProject.specModules && Object.keys(state.currentProject.specModules).length > 0 && (state.currentProject.specModules['product'] || state.currentProject.specModules['product.md']);
    const exploreBtn = document.getElementById('btn-explore-finish-wizard');
    const copilotPanel = document.getElementById('workspace-copilot-panel');

    if (!hasGeneratedSpecs) {
        if (exploreBtn) exploreBtn.classList.remove('hidden');
        if (copilotPanel) {
            copilotPanel.classList.remove('hidden');
            copilotPanel.classList.add('expanded');
        }
    } else {
        if (exploreBtn) exploreBtn.classList.add('hidden');
    }
}

// Renderizar el árbol lateral de especificaciones
function renderSpecTree() {
    const nav = document.getElementById('spec-tree-nav');
    nav.innerHTML = '';
    
    // 1. Renderizar especificaciones fijas (SPEC_FILES)
    SPEC_FILES.forEach(file => {
        const item = document.createElement('div');
        item.className = `spec-tree-item ${state.activeSpecFile === file.name ? 'active' : ''}`;
        
        let statusClass = 'status-pending';
        if (file.status === 'completed') statusClass = 'status-completed';
        if (file.status === 'error') statusClass = 'status-error';
        
        item.innerHTML = `
            <div class="spec-item-left">
                <i class="fa-solid ${file.icon}"></i>
                <span>${file.label}</span>
            </div>
            <span class="spec-status-indicator ${statusClass}"></span>
        `;
        
        item.addEventListener('click', () => {
            selectSpecFile(file.name);
        });
        
        nav.appendChild(item);
    });
    
    // 2. Renderizar características dinámicas si existen
    const featuresList = state.currentProject.featuresList || [];
    if (featuresList.length > 0) {
        const header = document.createElement('div');
        header.className = 'spec-tree-header-sep';
        header.style.cssText = "padding: var(--spacing-sm) var(--spacing-md); font-size: 11px; font-weight: bold; color: var(--text-secondary); text-transform: uppercase; margin-top: var(--spacing-md); border-top: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between;";
        header.innerHTML = `<span>Features & Módulos</span> <span class="badge" style="font-size:9px; background:rgba(255,255,255,0.05); padding:1px 5px; border-radius:3px;">${featuresList.length}</span>`;
        nav.appendChild(header);
        
        // Agrupar por carpeta temática
        const folders = {};
        featuresList.forEach(feat => {
            const fName = feat.folder || 'general';
            if (!folders[fName]) folders[fName] = [];
            folders[fName].push(feat);
        });
        
        Object.keys(folders).forEach(folderName => {
            const folderItem = document.createElement('div');
            folderItem.className = 'spec-tree-folder';
            folderItem.style.cssText = "padding: 6px 16px; font-size: 12px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 8px;";
            folderItem.innerHTML = `<i class="fa-solid fa-folder-open" style="color: var(--primary); font-size: 11px;"></i> <span>features/${folderName}</span>`;
            nav.appendChild(folderItem);
            
            folders[folderName].forEach(feat => {
                const fItem = document.createElement('div');
                fItem.className = `spec-tree-item feature-item ${state.activeSpecFile === feat.filename ? 'active' : ''}`;
                fItem.style.paddingLeft = "28px";
                fItem.innerHTML = `
                    <div class="spec-item-left">
                        <i class="fa-regular fa-file-code" style="font-size: 11px;"></i>
                        <span>${feat.title || feat.filename}</span>
                    </div>
                `;
                fItem.addEventListener('click', () => {
                    selectSpecFile(feat.filename);
                });
                nav.appendChild(fItem);
            });
        });
    }
}

// Seleccionar un archivo de especificación en el editor
function selectSpecFile(filename) {
    state.activeSpecFile = filename;
    document.getElementById('active-spec-title').innerText = filename;
    
    renderSpecTree();
    updateSpecInfoBanner(filename);

    const moduleName = filename.replace('.md', '').replace('.json', '');
    const mdContent = (state.currentProject.specModules && state.currentProject.specModules[moduleName]) || '';
    renderMarkdownHTML(mdContent);
}

// Actualizar información del banner contextual en el editor
function updateSpecInfoBanner(filename) {
    const doc = SPEC_DOCS[filename];
    if (!doc) return;
    
    const catBadge = document.getElementById('banner-category-badge');
    const docTitle = document.getElementById('banner-doc-title');
    const docDesc = document.getElementById('banner-doc-desc');
    
    if (catBadge) catBadge.innerText = doc.categoryLabel;
    if (docTitle) docTitle.innerText = filename;
    if (docDesc) docDesc.innerText = doc.desc;
}

// Renderizar la cuadrícula de tarjetas de especificaciones en el Onboarding Modal
function renderOnboardingGrid(filterCategory = 'all') {
    const container = document.getElementById('onboarding-grid-container');
    if (!container) return;

    container.innerHTML = '';

    Object.keys(SPEC_DOCS).forEach(fname => {
        const doc = SPEC_DOCS[fname];
        if (filterCategory && filterCategory !== 'all' && doc.category !== filterCategory) return;

        const card = document.createElement('div');
        card.className = 'onboarding-card';
        card.innerHTML = `
            <div class="onboarding-card-header">
                <div class="onboarding-card-title">
                    <i class="fa-solid ${doc.icon}"></i>
                    <span>${fname}</span>
                </div>
                <span class="badge">${doc.categoryLabel}</span>
            </div>
            <div style="font-weight: 600; font-size: 13px; color: var(--text-primary); margin-top: 2px;">${doc.title}</div>
            <p class="onboarding-card-desc">${doc.desc}</p>
            <div style="font-size: 12px; color: var(--text-secondary); background: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                <strong>Contenido & Función:</strong> ${doc.details}
            </div>
            <div class="onboarding-card-footer">
                <span><i class="fa-solid fa-microchip"></i> Consumidor: <strong>${doc.consumer}</strong></span>
            </div>
        `;

        container.appendChild(card);
    });
}

// Parser Markdown utilizando la librería Marked.js para previsualización HTML completa
function renderMarkdownHTML(md) {
    const pane = document.getElementById('markdown-preview-pane');
    if (!md || !md.trim()) {
        pane.innerHTML = `
            <div class="empty-spec-state" style="text-align: center; padding: 48px var(--spacing-lg); background: rgba(255,255,255,0.015); border: 1px dashed var(--border-color); border-radius: var(--radius-lg); margin-top: 20px;">
                <div style="width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(59,130,246,0.2)); display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto;">
                    <i class="fa-solid fa-comments" style="font-size: 24px; color: #10b981;"></i>
                </div>
                <h3 style="margin-bottom: 8px; font-weight: 700; color: var(--text-primary);">Fase de Exploración en Curso</h3>
                <p style="color: var(--text-secondary); max-width: 540px; margin: 0 auto 20px auto; font-size: 13.5px; line-height: 1.6;">
                    Estás definiendo la idea de "<strong>${(state.currentProject && state.currentProject.name) || 'Sin título'}</strong>" con el <strong>Spec Copilot</strong>. <br>
                    Cuando termines la charla previa, presiona el botón verde a continuación para que la IA pre-llene tu cuestionario y redacte las especificaciones.
                </p>
                <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                    <button id="btn-empty-open-chat" class="btn btn-border" style="padding: 10px 16px;">
                        <i class="fa-solid fa-comments" style="color: var(--primary);"></i> 💬 Abrir Explore Chat
                    </button>
                    <button id="btn-empty-review-wizard" class="btn btn-primary" style="background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; padding: 10px 20px; font-weight: 600;">
                        <i class="fa-solid fa-clipboard-check"></i> 📋 Revisar Cuestionario & Redactar Specs
                    </button>
                    <button id="btn-generate-specs-now" class="btn btn-border" style="padding: 10px 16px;">
                        <i class="fa-solid fa-bolt"></i> Generar Specs Directamente
                    </button>
                </div>
            </div>
        `;

        const openChatBtn = document.getElementById('btn-empty-open-chat');
        if (openChatBtn) {
            openChatBtn.addEventListener('click', () => {
                const panel = document.getElementById('workspace-copilot-panel');
                if (panel) {
                    panel.classList.remove('hidden');
                    panel.classList.add('expanded');
                }
            });
        }

        const reviewBtn = document.getElementById('btn-empty-review-wizard');
        if (reviewBtn) reviewBtn.addEventListener('click', extractAnswersAndLaunchWizard);

        const genNowBtn = document.getElementById('btn-generate-specs-now');
        if (genNowBtn) genNowBtn.addEventListener('click', exportSpecsToDisk);
        return;
    }
    
    // Si es un archivo JSON, lo renderizamos como código formateado
    if (state.activeSpecFile.endsWith('.json')) {
        let escaped = md
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        pane.innerHTML = `<pre class="json-preview" style="background-color: rgba(0,0,0,0.2); padding: 15px; border-radius: 6px; font-family: 'Fira Code', monospace; font-size: 13px; color: #a9b1d6; overflow-x: auto; white-space: pre-wrap; max-height: 500px; border: 1px solid var(--border-color);"><code class="language-json">${escaped}</code></pre>`;
        return;
    }
    
    try {
        // Permitimos saltos de línea y formateo GFM nativo (Tablas, etc)
        marked.setOptions({
            breaks: true,
            gfm: true
        });
        pane.innerHTML = marked.parse(md);
    } catch (e) {
        console.error("Error parsing with marked.js:", e);
        // Fallback simple si la CDN no carga
        let html = md
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\n/g, '<br>');
        pane.innerHTML = html;
    }
}

// Completar la sección activa usando Gemini
async function autocompleteActiveSection() {
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    const filename = state.activeSpecFile;
    const moduleName = filename.replace('.md', '').replace('.json', '');
    
    showToast(`Gemini está redactando ${filename}...`, "info");
    
    try {
        const response = await fetch('/api/autocomplete-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ 
                project_data: state.currentProject,
                filename: filename
            })
        });
        
        const data = await response.json();
        if (data.status === 'success' && data.project) {
            state.currentProject = data.project;
            const mdContent = state.currentProject.specModules[moduleName] || '';
            renderMarkdownHTML(mdContent);
            showToast(`${filename} redactado con éxito`, "success");
            updateGlobalProgressBar();
        } else {
            throw new Error(data.message || "Error al redactar la sección");
        }
    } catch (e) {
        console.error(e);
        showToast("Error al autocompletar sección con la IA", "error");
    }
}

// Generar y copiar un prompt formateado para Open Code / Cursor / Cline
function copyAgentPrompt(overrideSpecKey = null) {
    const fileKey = overrideSpecKey || state.activeSpecFile;
    if (!fileKey) {
        showToast("Selecciona un archivo de especificación primero", "info");
        return;
    }
    
    let relPath = fileKey;
    if (!relPath.endsWith('.md') && !relPath.endsWith('.json')) {
        relPath += '.md';
    }
    if (!relPath.startsWith('specs/')) {
        relPath = `specs/${relPath}`;
    }
    
    let promptText = "";
    if (relPath.includes("features/")) {
        promptText = `Tu Fuente Única de Verdad es la carpeta /specs del proyecto. Lee detenidamente la especificación de feature en "${relPath}" e implementa las Historias de Usuario, Criterios de Aceptación (GIVEN/WHEN/THEN) y Casos de Error en el código de la aplicación dentro de /agendapro.`;
    } else if (relPath.includes("database")) {
        promptText = `Lee la especificación de base de datos en "${relPath}" y aplica los cambios en los esquemas, migraciones o modelos de datos del proyecto dentro de /agendapro.`;
    } else if (relPath.includes("api") || relPath.includes("openapi")) {
        promptText = `Lee la especificación de la API en "${relPath}" e implementa o actualiza los endpoints, controladores y validaciones de entrada en /agendapro.`;
    } else {
        promptText = `Lee la especificación en "${relPath}" e implementa o ajusta el código correspondiente en la aplicación dentro de /agendapro siguiendo las reglas del proyecto.`;
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(promptText).then(() => {
            showToast("📋 ¡Prompt copiado al portapapeles! Pegalo en Open Code o Cursor.", "success");
        }).catch(err => {
            console.error("Error al copiar al portapapeles:", err);
            showToast("Prompt generado. Revisa la consola.", "info");
        });
    } else {
        showToast("¡Prompt generado! " + promptText, "info");
    }
}

// Guardar el proyecto localmente en la carpeta del backend
async function saveProjectToServer() {
    state.currentProject.updatedAt = Date.now();
    try {
        const response = await fetch('/api/save-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_data: state.currentProject })
        });
        const data = await response.json();
        if (data.status === 'success') {
            console.log("Proyecto auto-guardado");
        }
    } catch (e) {
        console.error("Error en auto-guardado:", e);
    }
}

// Exportar las especificaciones y escribirlas en el disco local
async function exportSpecsToDisk() {
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    showToast("Redactando y compilando archivos en /specs...", "info");
    await saveProjectToServer();
    startPollingGenerationStatus();
    
    try {
        const response = await fetch('/api/export-specs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ project_data: state.currentProject })
        });
        const data = await response.json();
        stopPollingGenerationStatus();

        if (data.status === 'success') {
            const loadResp = await fetch('/api/load-project');
            const loadData = await loadResp.json();
            if (loadData.status === 'success' && loadData.project) {
                state.currentProject = loadData.project;
            }
            showToast("Especificaciones redactadas y guardadas con éxito en la carpeta del proyecto", "success");
            loadWorkspace();
        } else {
            showToast("Hubo un error al generar las especificaciones", "error");
        }
    } catch (e) {
        stopPollingGenerationStatus();
        console.error(e);
        showToast("Error al exportar especificaciones", "error");
    }
}

// Panel de visualización de especificaciones limpio

// Sistema de Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-circle-xmark';
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remover después de 3.5 segundos
    setTimeout(() => {
        toast.style.animation = 'fadeIn 0.3s ease reverse forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

// switchEditorView eliminada

// Cambiar estado visual del modal de planificación
function showPlanningState(stateName) {
    document.querySelectorAll('.planning-state').forEach(el => el.classList.add('hidden'));
    const stateEl = document.getElementById(`planning-state-${stateName}`);
    if (stateEl) stateEl.classList.remove('hidden');
}

// Analizar proyecto para sugerir features
async function runPlanningAnalysis() {
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    const customInputEl = document.getElementById('planning-custom-input');
    const customFeatureVal = customInputEl ? customInputEl.value.trim() : '';

    showPlanningState('loading-list');
    
    try {
        const response = await fetch('/api/plan-features', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ 
                project_data: state.currentProject,
                custom_feature: customFeatureVal
            })
        });
        
        const data = await response.json();
        if (data.status === 'success' || data.status === 'fallback') {
            const features = data.features || [];
            displayFeaturesChecklist(features);
            showPlanningState('list');
        } else {
            showToast("Error al planificar features: " + data.message, "error");
            showPlanningState('initial');
        }
    } catch (err) {
        showToast("Error de conexión al planificar features", "error");
        showPlanningState('initial');
    }
}

// Mostrar checklist de features encontradas
function displayFeaturesChecklist(features) {
    const container = document.getElementById('features-checklist-container');
    container.innerHTML = '';
    
    features.forEach(feat => {
        const item = document.createElement('div');
        item.className = 'feature-checklist-item';
        
        item.innerHTML = `
            <input type="checkbox" id="chk-feat-${feat.id}" data-id="${feat.id}" data-name="${feat.name}" data-desc="${feat.description}" data-folder="${feat.folder}" checked>
            <div class="feature-item-text">
                <div class="feature-item-title">${feat.name}</div>
                <div class="feature-item-desc">${feat.description}</div>
                <div class="feature-item-folder">features/${feat.folder}</div>
            </div>
        `;
        
        item.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                const chk = item.querySelector('input[type="checkbox"]');
                chk.checked = !chk.checked;
            }
        });
        
        container.appendChild(item);
    });
}

// Procesar y generar individualmente las features seleccionadas
async function submitFeatureGeneration() {
    const checkboxes = document.querySelectorAll('#features-checklist-container input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        showToast("Selecciona al menos una feature para generar", "error");
        return;
    }
    
    const featuresToGenerate = Array.from(checkboxes).map(chk => ({
        id: chk.dataset.id,
        name: chk.dataset.name,
        description: chk.dataset.desc,
        folder: chk.dataset.folder
    }));
    
    showPlanningState('generating');
    
    const logContainer = document.getElementById('generation-log-container');
    logContainer.innerHTML = '';
    
    const total = featuresToGenerate.length;
    let completed = 0;
    
    for (let i = 0; i < total; i++) {
        const feat = featuresToGenerate[i];
        
        document.getElementById('generation-progress-text').innerText = `Generando feature ${i+1} de ${total}: ${feat.name}...`;
        const progressPercent = Math.round((i / total) * 100);
        document.getElementById('planning-progress-fill').style.width = `${progressPercent}%`;
        
        const logItem = document.createElement('div');
        logItem.className = 'log-item loading';
        logItem.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Generando ${feat.name}...</span>`;
        logContainer.appendChild(logItem);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        try {
            const response = await fetch('/api/generate-feature', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': state.apiKey
                },
                body: JSON.stringify({
                    project_data: state.currentProject,
                    feature: feat
                })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                logItem.className = 'log-item success';
                logItem.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>¡Listo! ${feat.name} guardado</span>`;
                state.currentProject = data.project_data;
                completed++;
            } else {
                logItem.className = 'log-item error';
                logItem.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> <span>Error en ${feat.name}</span>`;
            }
        } catch (err) {
            logItem.className = 'log-item error';
            logItem.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> <span>Error de red en ${feat.name}</span>`;
        }
    }
    
    document.getElementById('generation-progress-text').innerText = `Proceso completado. ${completed} de ${total} features generadas con éxito.`;
    document.getElementById('planning-progress-fill').style.width = `100%`;
    
    // Cargar proyecto completo sincronizado desde el servidor
    try {
        const loadResp = await fetch('/api/load-project');
        const loadData = await loadResp.json();
        if (loadData.status === 'success' && loadData.project) {
            state.currentProject = loadData.project;
        }
    } catch (e) {
        console.error("Error re-cargando proyecto:", e);
    }

    renderSpecTree();

    // Seleccionar automáticamente la última feature generada para abrirla en el editor
    if (featuresToGenerate.length > 0) {
        const lastFeat = featuresToGenerate[featuresToGenerate.length - 1];
        const lastKey = `features/${lastFeat.folder}/${lastFeat.id}`;
        selectSpecFile(lastKey);
    }

    showToast(`¡Proceso completado! ${completed} de ${total} features generadas.`, "success");

    const planningModal = document.getElementById('planning-modal');
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-primary btn-full-width';
    closeBtn.style.marginTop = '16px';
    closeBtn.innerHTML = '<i class="fa-solid fa-check"></i> Cerrar y Ver en Workspace';
    closeBtn.addEventListener('click', () => {
        planningModal.classList.add('hidden');
        showPlanningState('initial');
    });
    logContainer.appendChild(closeBtn);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Auto-cerrar el modal suavemente tras 1.2s para una UX óptima
    setTimeout(() => {
        if (!planningModal.classList.contains('hidden')) {
            planningModal.classList.add('hidden');
            showPlanningState('initial');
        }
    }, 1200);
}

// Consultar progreso de generación de especificaciones en tiempo real
let generationPollInterval = null;

function startPollingGenerationStatus() {
    const container = document.getElementById('loader-progress-container');
    if (container) container.classList.remove('hidden');

    if (generationPollInterval) clearInterval(generationPollInterval);

    generationPollInterval = setInterval(async () => {
        try {
            const resp = await fetch('/api/generation-status');
            const data = await resp.json();
            
            if (data.is_generating || (data.completed_files && data.completed_files.length > 0)) {
                const total = data.total_files || 17;
                const completedCount = data.completed_files ? data.completed_files.length : 0;
                const remaining = total - completedCount;
                const percent = data.percent || Math.round((completedCount / total) * 100);
                
                const curFileEl = document.getElementById('loader-current-file');
                if (curFileEl) {
                    curFileEl.innerHTML = data.current_filename 
                        ? `<i class="fa-solid fa-spinner fa-spin" style="margin-right: 6px; color: var(--primary);"></i> Redactando con IA: <strong style="color: var(--text-primary);">${data.current_filename}</strong>`
                        : `Procesando especificaciones...`;
                }

                const statusTextEl = document.getElementById('loader-status-text');
                if (statusTextEl) {
                    statusTextEl.innerText = data.current_filename 
                        ? `La IA está redactando ${data.current_filename} (${completedCount + 1} de ${total})...`
                        : `Generando los 17 archivos de especificación en formato Markdown...`;
                }

                const badgeEl = document.getElementById('loader-percent-badge');
                if (badgeEl) badgeEl.innerText = `${percent}%`;

                const fillEl = document.getElementById('loader-progress-bar-fill');
                if (fillEl) fillEl.style.width = `${percent}%`;

                const countEl = document.getElementById('loader-count-text');
                if (countEl) countEl.innerText = `${completedCount} de ${total} listos en disco`;

                const remEl = document.getElementById('loader-remaining-text');
                if (remEl) remEl.innerText = `Faltan ${remaining > 0 ? remaining : 0} archivos`;

                const chipsContainer = document.getElementById('loader-completed-chips');
                if (chipsContainer) {
                    let chipsHtml = '';
                    if (data.completed_files && data.completed_files.length > 0) {
                        chipsHtml += data.completed_files.map(f => 
                            `<span style="font-size: 11px; background: rgba(0, 230, 118, 0.15); color: #00e676; padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(0, 230, 118, 0.3);"><i class="fa-solid fa-check"></i> ${f}</span>`
                        ).join('');
                    }
                    if (data.current_filename && (!data.completed_files || !data.completed_files.includes(data.current_filename))) {
                        chipsHtml += `<span style="font-size: 11px; background: rgba(123, 97, 255, 0.2); color: var(--primary-hover); padding: 2px 8px; border-radius: 12px; border: 1px solid var(--primary);"><i class="fa-solid fa-spinner fa-spin"></i> ${data.current_filename}</span>`;
                    }
                    chipsContainer.innerHTML = chipsHtml;
                }
            }
        } catch (e) {
            console.error("Error consultando estado de generación:", e);
        }
    }, 1000);
}

function stopPollingGenerationStatus() {
    if (generationPollInterval) {
        clearInterval(generationPollInterval);
        generationPollInterval = null;
    }
    const container = document.getElementById('loader-progress-container');
    if (container) container.classList.add('hidden');
}

/* ==========================================================================
   SPEC COPILOT CHAT LOGIC
   ========================================================================== */

function toggleCopilotPanel() {
    const panel = document.getElementById('workspace-copilot-panel');
    if (!panel) return;
    panel.classList.toggle('hidden');
}

async function loadCopilotHistory() {
    try {
        const resp = await fetch('/api/copilot-history');
        const data = await resp.json();
        if (data.status === 'success' && data.history && data.history.length > 0) {
            state.copilotHistory = data.history;
            const container = document.getElementById('copilot-messages');
            if (container) {
                container.innerHTML = '';
                data.history.forEach(msg => {
                    const role = (msg.role === 'user') ? 'user' : 'ai';
                    appendCopilotMsg(role, msg.content, false);
                });
                container.scrollTop = container.scrollHeight;
            }
        }
    } catch (e) {
        console.error("Error cargando historial de chat:", e);
    }
}

async function clearCopilotChat() {
    state.copilotHistory = [];
    try {
        await fetch('/api/copilot-clear-history', { method: 'POST' });
    } catch (e) {
        console.error("Error al limpiar el historial en servidor:", e);
    }
    const container = document.getElementById('copilot-messages');
    if (container) {
        container.innerHTML = `
            <div class="copilot-msg msg-ai">
                <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="msg-body">
                    <p>Conversación reiniciada. ¿En qué más puedo ayudarte sobre las especificaciones del proyecto?</p>
                </div>
            </div>
        `;
    }
}

async function sendCopilotMessage(queryText) {
    const inputEl = document.getElementById('copilot-input');
    const text = queryText || (inputEl ? inputEl.value.trim() : '');
    if (!text) return;

    if (inputEl) {
        inputEl.value = '';
        inputEl.style.height = 'auto';
    }

    const container = document.getElementById('copilot-messages');
    if (!container) return;

    // 1. Renderizar mensaje del usuario
    appendCopilotMsg('user', text);

    // 2. Renderizar indicador "Pensando..."
    const typingId = appendCopilotTyping();

    try {
        const resp = await fetch('/api/copilot-chat', {
            method: 'POST',
            headers: getAiHeaders(),
            body: JSON.stringify({
                message: text,
                history: state.copilotHistory || [],
                project_data: state.currentProject
            })
        });

        const isQuota = await checkResponseForQuotaError(resp, () => sendCopilotMessage(text));
        if (isQuota) {
            removeCopilotTyping(typingId);
            appendCopilotMsg('ai', `⚠️ Límite de cuota (429/Rate Limit) alcanzado. Puedes ingresar una clave de resguardo o cambiar de modelo en el pop-up.`);
            return;
        }

        const data = await resp.json();
        removeCopilotTyping(typingId);

        if (data.status === 'success' && data.reply) {
            if (data.history) {
                state.copilotHistory = data.history;
            } else {
                if (!state.copilotHistory) state.copilotHistory = [];
                state.copilotHistory.push({ role: 'user', content: text });
                state.copilotHistory.push({ role: 'model', content: data.reply });
            }

            appendCopilotMsg('ai', data.reply);
        } else {
            const errDetail = data.detail || data.message || "Error al comunicarse con el Copilot.";
            appendCopilotMsg('ai', `⚠️ ${errDetail}`);
        }
    } catch (e) {
        removeCopilotTyping(typingId);
        console.error("Error en sendCopilotMessage:", e);
        appendCopilotMsg('ai', `⚠️ Error de conexión: ${e.message}`);
    }
}

function appendCopilotMsg(role, text, autoScroll = true) {
    const container = document.getElementById('copilot-messages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `copilot-msg msg-${role}`;

    const parsedHTML = (typeof marked !== 'undefined' && marked.parse) ? marked.parse(text) : `<p>${text}</p>`;

    msgDiv.innerHTML = `
        <div class="msg-avatar">
            <i class="fa-solid ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i>
        </div>
        <div class="msg-body">
            ${parsedHTML}
        </div>
    `;

    container.appendChild(msgDiv);
    if (autoScroll) {
        container.scrollTop = container.scrollHeight;
    }
}

function appendCopilotTyping() {
    const container = document.getElementById('copilot-messages');
    if (!container) return null;

    // Remover indicadores previos por seguridad
    document.querySelectorAll('.copilot-typing-msg').forEach(el => el.remove());

    const typingId = 'copilot-typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = typingId;
    msgDiv.className = 'copilot-msg msg-ai copilot-typing-msg';
    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-robot" style="color: var(--primary);"></i></div>
        <div class="msg-body" style="font-style: italic; color: var(--text-secondary); display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-circle-notch fa-spin" style="color: var(--accent); font-size: 14px;"></i>
            <span>Spec Copilot analizando respuesta...</span>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return typingId;
}

function removeCopilotTyping(typingId) {
    if (typingId) {
        const el = document.getElementById(typingId);
        if (el) el.remove();
    }
    document.querySelectorAll('.copilot-typing-msg').forEach(el => el.remove());
}
