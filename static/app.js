/**
 * ==========================================================================
 * SPEC IDE CLIENT SIDE - VANILLA JS CORE
 * ==========================================================================
 */

// Estado Global de la Aplicación
const state = {
    apiKey: '',
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
    isDarkTheme: true,
    hasBackendApiKey: false,
    generationPath: 'guided'
};

// Estructura fija de los 16 archivos de la spec
const SPEC_FILES = [
    { name: 'project.md', label: 'Ficha Técnica', icon: 'fa-file-signature', status: 'completed' },
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
    { name: 'agents.md', label: 'Instrucciones IA', icon: 'fa-robot', status: 'completed' }
];

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
    
    // Intentar cargar proyecto existente del backend
    await checkExistingProject();
}

// Cargar configuraciones del almacenamiento local
function loadSettings() {
    state.apiKey = localStorage.getItem('gemini_api_key') || '';
    document.getElementById('gemini-api-key').value = state.apiKey;
    
    const theme = localStorage.getItem('theme');
    if (theme === 'light') {
        state.isDarkTheme = false;
    }
}

// Verificar si el servidor ya tiene la API Key configurada
async function checkBackendConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        state.hasBackendApiKey = data.hasApiKey;
        
        const keyInput = document.getElementById('gemini-api-key');
        if (state.hasBackendApiKey) {
            if (!state.apiKey) {
                keyInput.placeholder = "Configurada en servidor (.env)";
                keyInput.value = "";
            } else {
                keyInput.placeholder = "Gemini API Key...";
            }
        }
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

// Comprobar si hay un proyecto activo guardado en el servidor Python
async function checkExistingProject() {
    try {
        const response = await fetch('/api/load-project');
        const data = await response.json();
        
        if (data.status === 'success' && data.project) {
            state.currentProject = data.project;
            renderRecentProject(data.project);
        } else {
            renderRecentProject(null);
        }
    } catch (e) {
        console.error("Error cargando proyecto:", e);
        renderRecentProject(null);
    }
}

// Mostrar proyecto en la lista de recientes
function renderRecentProject(project) {
    const container = document.getElementById('recent-projects-list');
    if (!project) {
        container.innerHTML = `
            <div class="empty-projects-state">
                <i class="fa-solid fa-diagram-project"></i>
                <p>No hay proyectos activos cargados. <br>Inicia uno nuevo para comenzar.</p>
            </div>
        `;
        return;
    }
    
    const dateStr = new Date(project.updatedAt || Date.now()).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    container.innerHTML = `
        <div class="recent-project-item" id="btn-load-recent-project">
            <div class="project-item-info">
                <span class="project-item-title">${project.name}</span>
                <span class="project-item-date">Modificado: ${dateStr}</span>
            </div>
            <div class="project-item-action">
                <i class="fa-solid fa-chevron-right"></i>
            </div>
        </div>
    `;
    
    document.getElementById('btn-load-recent-project').addEventListener('click', () => {
        loadWorkspace();
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

    // Guardar API Key de Gemini
    document.getElementById('save-api-key-btn').addEventListener('click', () => {
        const key = document.getElementById('gemini-api-key').value.trim();
        state.apiKey = key;
        localStorage.setItem('gemini_api_key', key);
        showToast("Clave API guardada localmente", "success");
    });

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

    // Exportar Specs
    document.getElementById('btn-export-specs').addEventListener('click', exportSpecsToDisk);

    // Modal de Planificación de Features
    const planningModal = document.getElementById('planning-modal');
    
    document.getElementById('btn-open-planning').addEventListener('click', () => {
        showPlanningState('initial');
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

    // Guardar Manual en Workspace
    document.getElementById('btn-save-project-manual').addEventListener('click', saveProjectToServer);

    // Completar con IA en el editor
    document.getElementById('btn-ai-autocomplete').addEventListener('click', autocompleteActiveSection);

    // Pestañas del Editor (Formulario vs Markdown)
    const editorTabs = document.querySelectorAll('.editor-tab');
    editorTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            editorTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const view = tab.dataset.view;
            document.querySelectorAll('.editor-tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`editor-view-${view}`).classList.add('active');
            
            if (view === 'markdown') {
                updateMarkdownPreview();
            }
        });
    });

    // Sincronizar edición manual de Markdown con respuestas del proyecto
    document.getElementById('markdown-raw-editor').addEventListener('input', (e) => {
        const text = e.target.value;
        renderMarkdownHTML(text);
        // Guardamos temporalmente en el estado
        state.currentProject.specModules[state.activeSpecFile.replace('.md', '').replace('.json', '')] = text;
    });

    // Pestañas del Inspector (Diagramas, Linter, Chat)
    const inspectorTabs = document.querySelectorAll('.inspector-tab');
    inspectorTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            inspectorTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const selectedTab = tab.dataset.tab;
            document.querySelectorAll('.inspector-tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`inspector-tab-${selectedTab}`).classList.add('active');
        });
    });

    // Regenerar Diagrama
    document.getElementById('btn-regenerate-diagram').addEventListener('click', generateDiagram);

    // Correr Linter de Spec
    document.getElementById('btn-run-linter').addEventListener('click', runConsistencyCheck);

    // Copiloto: Enviar mensaje
    document.getElementById('chat-send-btn').addEventListener('click', sendCopilotMessage);
    document.getElementById('chat-user-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendCopilotMessage();
        }
    });
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
    const total = SPEC_FILES.length - 2; // Excluimos Ficha Técnica y Prompt de Agente (que son automáticas)
    let completed = 0;
    
    SPEC_FILES.forEach(file => {
        if (file.name !== 'project.md' && file.name !== 'agents.md') {
            const hasContent = state.currentProject.answers[file.name] || 
                                (state.currentProject.specModules && state.currentProject.specModules[file.name.replace('.md', '').replace('.json', '')]);
            if (hasContent) {
                file.status = 'completed';
                completed++;
            } else {
                file.status = 'pending';
            }
        }
    });
    
    const percentage = Math.round((completed / total) * 100);
    document.getElementById('progress-percent').innerText = `${percentage}%`;
    document.getElementById('progress-fill-bar').style.width = `${percentage}%`;
    
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
    
    showScreen('screen-discovery');
    document.getElementById('discovery-loader').classList.remove('hidden');
    document.getElementById('wizard-container').classList.add('hidden');
    
    if (state.generationPath === 'direct') {
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
            
            // Actualizar panel lateral conceptual
            updateConceptualAnalysisPanel();
            
            // 2. Generar directamente las especificaciones con la IA
            document.getElementById('loader-status-text').innerText = "Generando los 16 archivos de especificación en formato Markdown... (Esto puede tardar unos segundos)";
            
            await saveProjectToServer(); // Guardar el proyecto en su estado inicial
            
            const exportResponse = await fetch('/api/export-specs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': state.apiKey
                },
                body: JSON.stringify({ project_data: state.currentProject })
            });
            
            const exportData = await exportResponse.json();
            if (exportData.status === 'success') {
                // Cargar el proyecto con todos los specModules cargados
                const loadResp = await fetch('/api/load-project');
                const loadData = await loadResp.json();
                
                if (loadData.status === 'success' && loadData.project) {
                    state.currentProject = loadData.project;
                }
                showToast("Especificaciones generadas directamente con éxito", "success");
                loadWorkspace();
            } else {
                throw new Error("La generación de especificaciones no devolvió éxito.");
            }
        } catch (e) {
            console.error(e);
            showToast("Error en la generación directa. Redirigiendo a pantalla de inicio.", "error");
            showScreen('screen-dashboard');
        }
    } else {
        // Camino 2: Entrevista Guiada
        document.getElementById('loader-status-text').innerText = "Gemini está formulando preguntas inteligentes para tu proyecto...";
        
        try {
            const response = await fetch('/api/analyze-idea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': state.apiKey
                },
                body: JSON.stringify({ idea: seedIdea })
            });
            
            const data = await response.json();
            
            // Cargar árbol de preguntas dinámicas y metadatos
            state.questionTree = data.questions || [];
            state.currentProject.metadata.domain = data.domain || 'Por definir';
            state.currentProject.metadata.productType = data.productType || 'SaaS';
            state.currentProject.metadata.actors = data.actors || [];
            state.currentProject.metadata.features = data.detectedFeatures || [];
            
            // Actualizar UI del panel lateral conceptual
            updateConceptualAnalysisPanel();
            
            // Iniciar Wizard
            state.activeQuestionIndex = 0;
            document.getElementById('discovery-loader').classList.add('hidden');
            document.getElementById('wizard-container').classList.remove('hidden');
            renderWizardQuestion();
            
        } catch (e) {
            console.error(e);
            showToast("Error de conexión con la IA. Se cargaron preguntas de fallback.", "error");
            document.getElementById('discovery-loader').classList.add('hidden');
            document.getElementById('wizard-container').classList.remove('hidden');
        }
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
    document.getElementById('wizard-step-indicator').innerText = `Pregunta ${state.activeQuestionIndex + 1} de ${state.questionTree.length}`;
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
        
        q.options.forEach(opt => {
            const item = document.createElement('div');
            item.className = `select-option-item ${prevAnswer === opt ? 'selected' : ''}`;
            item.innerHTML = `<i class="fa-regular ${prevAnswer === opt ? 'fa-circle-dot' : 'fa-circle'}"></i> <span>${opt}</span>`;
            item.addEventListener('click', () => {
                // Deseleccionar hermanos
                grid.querySelectorAll('.select-option-item').forEach(el => el.classList.remove('selected'));
                grid.querySelectorAll('i').forEach(i => {
                    i.className = 'fa-regular fa-circle';
                });
                
                item.classList.add('selected');
                item.querySelector('i').className = 'fa-solid fa-circle-dot';
                state.currentProject.answers[q.id] = opt;
            });
            grid.appendChild(item);
        });
        inputContainer.appendChild(grid);
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
            // No hay más preguntas, saltamos al Workspace
            loadWorkspace();
        }
    } catch (e) {
        console.error(e);
        loadWorkspace();
    }
}

// Carga del Workspace IDE
function loadWorkspace() {
    showScreen('screen-workspace');
    selectSpecFile('product.md');
    saveProjectToServer();
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
            folderItem.innerHTML = `<i class="fa-solid fa-folder-open" style="color: var(--primary-color); font-size: 11px;"></i> <span>features/${folderName}</span>`;
            nav.appendChild(folderItem);
            
            folders[folderName].forEach(feat => {
                const fileKey = `features/${folderName}/${feat.id}`;
                const item = document.createElement('div');
                item.className = `spec-tree-item ${state.activeSpecFile === fileKey ? 'active' : ''}`;
                item.style.paddingLeft = '32px';
                
                item.innerHTML = `
                    <div class="spec-item-left">
                        <i class="fa-regular fa-file-lines" style="font-size: 11px;"></i>
                        <span>${feat.name}</span>
                    </div>
                    <span class="spec-status-indicator status-completed"></span>
                `;
                
                item.addEventListener('click', () => {
                    selectSpecFile(fileKey);
                });
                
                nav.appendChild(item);
            });
        });
    }
}

// Seleccionar archivo activo en el IDE
function selectSpecFile(filename) {
    state.activeSpecFile = filename;
    document.getElementById('active-spec-title').innerText = filename;
    
    // Cambiar clase activa en el árbol
    renderSpecTree();
    
    // Cargar cuestionario o editor Markdown
    const formContainer = document.getElementById('active-spec-form-container');
    formContainer.innerHTML = '';
    
    const isFeature = filename.startsWith('features/');
    const formTab = Array.from(document.querySelectorAll('.editor-tab')).find(t => t.dataset.view === 'form');
    
    if (isFeature) {
        if (formTab) formTab.classList.add('hidden');
        switchEditorView('markdown');
        
        // Cargar contenido de la feature
        const mdContent = state.currentProject.specModules[filename] || '';
        document.getElementById('markdown-raw-editor').value = mdContent;
        renderMarkdownHTML(mdContent);
        
    } else {
        if (formTab) formTab.classList.remove('hidden');
        switchEditorView('form');
        
        // Buscamos preguntas previas del Wizard de esta categoría
        const fileCategoryMap = {
            'product.md': 'Producto',
            'requirements.md': 'Requisitos',
            'architecture.md': 'Arquitectura',
            'database.md': 'Base de datos',
            'api.md': 'API',
            'security.md': 'Seguridad',
            'roadmap.md': 'General'
        };
        
        const cat = fileCategoryMap[filename] || '';
        const relevantQuestions = state.questionTree.filter(q => q.section === cat);
        
        if (relevantQuestions.length > 0) {
            const title = document.createElement('h3');
            title.innerText = `Datos estructurados - ${cat}`;
            formContainer.appendChild(title);
            
            relevantQuestions.forEach(q => {
                const formGroup = document.createElement('div');
                formGroup.className = 'form-group';
                
                const label = document.createElement('label');
                label.innerText = q.label;
                formGroup.appendChild(label);
                
                const val = state.currentProject.answers[q.id] || '';
                
                if (q.type === 'select') {
                    const select = document.createElement('select');
                    select.style.padding = '12px';
                    select.style.backgroundColor = 'rgba(255,255,255,0.04)';
                    select.style.color = 'var(--text-primary)';
                    select.style.border = '1px solid var(--border-color)';
                    select.style.borderRadius = '8px';
                    select.style.outline = 'none';
                    
                    q.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt;
                        option.text = opt;
                        if (opt === val) option.selected = true;
                        select.appendChild(option);
                    });
                    
                    select.addEventListener('change', (e) => {
                        state.currentProject.answers[q.id] = e.target.value;
                        updateGlobalProgressBar();
                    });
                    formGroup.appendChild(select);
                } else {
                    const input = document.createElement('textarea');
                    input.value = val;
                    input.addEventListener('input', (e) => {
                        state.currentProject.answers[q.id] = e.target.value;
                        updateGlobalProgressBar();
                    });
                    formGroup.appendChild(input);
                }
                formContainer.appendChild(formGroup);
            });
        } else {
            formContainer.innerHTML = `
                <div class="empty-projects-state">
                    <i class="fa-solid fa-file-signature" style="font-size: 32px;"></i>
                    <h3>Sección Libre</h3>
                    <p>Usa la pestaña "Visualizar Markdown" o haz clic en "Completar con IA" para redactar esta especificación.</p>
                </div>
            `;
        }
        
        // Cargar contenido Markdown en el editor raw
        const moduleName = filename.replace('.md', '').replace('.json', '');
        const mdContent = (state.currentProject.specModules && state.currentProject.specModules[moduleName]) || '';
        document.getElementById('markdown-raw-editor').value = mdContent;
        renderMarkdownHTML(mdContent);
    }
}

// Actualizar la pestaña de Markdown Preview
function updateMarkdownPreview() {
    const filename = state.activeSpecFile;
    const moduleName = filename.replace('.md', '').replace('.json', '');
    const currentText = document.getElementById('markdown-raw-editor').value;
    
    state.currentProject.specModules = state.currentProject.specModules || {};
    state.currentProject.specModules[moduleName] = currentText;
    
    renderMarkdownHTML(currentText);
}

// Parser Markdown sumamente simple para previsualización HTML
function renderMarkdownHTML(md) {
    const pane = document.getElementById('markdown-preview-pane');
    if (!md) {
        pane.innerHTML = '<p style="color: var(--text-muted); font-style: italic;">Sin contenido generado aún. Haz clic en "Completar con IA" para redactar esta sección.</p>';
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
    
    // Reemplazo básico de etiquetas Markdown
    let html = md
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        .replace(/`([^`]+)`/gim, '<code>$1</code>')
        .replace(/\n$/gim, '<br>');

    // Agrupar elementos li en ul
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    
    pane.innerHTML = html;
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
        const response = await fetch('/api/export-specs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ project_data: state.currentProject })
        });
        
        // Recargar el archivo especificado
        const loadResp = await fetch('/api/load-project');
        const loadData = await loadResp.json();
        
        if (loadData.status === 'success' && loadData.project) {
            state.currentProject = loadData.project;
            const mdContent = state.currentProject.specModules[moduleName] || '';
            document.getElementById('markdown-raw-editor').value = mdContent;
            renderMarkdownHTML(mdContent);
            showToast(`${filename} redactado con éxito`, "success");
            updateGlobalProgressBar();
        }
    } catch (e) {
        console.error(e);
        showToast("Error al autocompletar sección con la IA", "error");
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
    
    showToast("Compilando y exportando directorio /specs...", "info");
    await saveProjectToServer();
    
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
        if (data.status === 'success') {
            showToast("Especificación exportada directamente al directorio /specs/ del proyecto", "success");
            updateGlobalProgressBar();
        }
    } catch (e) {
        console.error(e);
        showToast("Error al exportar especificaciones", "error");
    }
}

// Generar diagrama Mermaid interactivo
async function generateDiagram() {
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    const type = document.getElementById('diagram-type-select').value;
    const viewer = document.getElementById('mermaid-diagram-viewer');
    
    viewer.innerHTML = '<div class="spinner"></div><p style="margin-top:10px; font-size:12px; color:var(--text-secondary);">Generando diagrama por IA...</p>';
    
    try {
        const response = await fetch('/api/generate-diagram', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({
                diagram_type: type,
                answers: state.currentProject.answers
            })
        });
        const data = await response.json();
        const code = data.code;
        
        viewer.innerHTML = `<pre class="mermaid" id="active-mermaid-element">${code}</pre>`;
        
        // Forzar renderizado de Mermaid
        const element = document.getElementById('active-mermaid-element');
        await mermaid.run({
            nodes: [element]
        });
        
    } catch (e) {
        console.error(e);
        viewer.innerHTML = `
            <div class="empty-diagram-state">
                <i class="fa-solid fa-circle-exclamation" style="color:var(--danger)"></i>
                <p>Error al renderizar el diagrama de Mermaid. <br>Revisa tu API key e inténtalo de nuevo.</p>
            </div>
        `;
    }
}

// Correr validador de consistencia (Linter)
async function runConsistencyCheck() {
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    const container = document.getElementById('linter-warnings-list');
    container.innerHTML = '<div class="spinner"></div><p style="margin-top:10px; font-size:12px; color:var(--text-secondary);">Analizando consistencia de la Spec...</p>';
    
    try {
        const response = await fetch('/api/check-consistency', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ project_data: state.currentProject })
        });
        const data = await response.json();
        const warnings = data.warnings || [];
        
        if (warnings.length === 0) {
            container.innerHTML = `
                <div class="empty-linter-state">
                    <i class="fa-solid fa-circle-check"></i>
                    <p>¡Cero inconsistencias detectadas! Tu especificación está completamente alineada.</p>
                </div>
            `;
            
            // Poner todos los estados de los módulos en completed/verdes
            SPEC_FILES.forEach(f => f.status = 'completed');
            renderSpecTree();
            return;
        }
        
        container.innerHTML = '';
        warnings.forEach(warn => {
            const el = document.createElement('div');
            el.className = `warning-item ${warn.severity}`;
            el.innerHTML = `
                <span class="warning-title">${warn.section} <mark>${warn.severity}</mark></span>
                <span class="warning-message">${warn.message}</span>
                <span class="warning-suggestion"><strong>Sugerencia:</strong> ${warn.suggestion}</span>
            `;
            container.appendChild(el);
            
            // Marcar módulos con error en la barra lateral si tienen alertas críticas
            if (warn.severity === 'critical') {
                const matchingFile = SPEC_FILES.find(f => f.label.toLowerCase().includes(warn.section.toLowerCase()) || f.name.toLowerCase().includes(warn.section.toLowerCase()));
                if (matchingFile) {
                    matchingFile.status = 'error';
                }
            }
        });
        
        renderSpecTree();
        showToast(`Linter completado: ${warnings.length} observaciones`, "info");
        
    } catch (e) {
        console.error(e);
        container.innerHTML = `
            <div class="empty-linter-state">
                <i class="fa-solid fa-triangle-exclamation" style="color:var(--danger)"></i>
                <p>Error en la conexión al validar consistencia.</p>
            </div>
        `;
    }
}

// Chat Copiloto interactivo
async function sendCopilotMessage() {
    const inputEl = document.getElementById('chat-user-input');
    const msg = inputEl.value.trim();
    if (!msg) return;
    
    if (!state.apiKey && !state.hasBackendApiKey) {
        showToast("Ingresa tu API Key de Gemini en el Header o configúrala en el servidor", "error");
        return;
    }
    
    inputEl.value = '';
    
    const chatContainer = document.getElementById('chat-messages-container');
    
    // Agregar mensaje del usuario
    const userMsgEl = document.createElement('div');
    userMsgEl.className = 'chat-message user';
    userMsgEl.innerHTML = `<p>${msg}</p>`;
    chatContainer.appendChild(userMsgEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Agregar spinner de carga de IA
    const loaderMsgEl = document.createElement('div');
    loaderMsgEl.className = 'chat-message ai';
    loaderMsgEl.innerHTML = `<div class="spinner" style="width:20px; height:20px;"></div>`;
    chatContainer.appendChild(loaderMsgEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    try {
        // Hacemos una llamada directa a Gemini para responder
        const response = await fetch('/api/next-questions', { // Reutilizamos un prompt de refinamiento
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({
                idea: `Contexto del Proyecto: ${state.currentProject.seedIdea}. Sección Activa: ${state.activeSpecFile}. Mensaje del usuario: ${msg}`,
                answers: state.currentProject.answers
            })
        });
        
        // En este prototipo rápido, simulamos una respuesta útil basada en el contexto para agilizar la interacción
        // Para que responda correctamente la IA al chat, implementaremos un endpoint simple o refinamos el prompt:
        const prompt = `
        Eres el Copiloto de Spec IDE.
        El usuario está diseñando el proyecto: "${state.currentProject.name}" con la idea semilla "${state.currentProject.seedIdea}".
        Estamos editando el archivo de especificación: "${state.activeSpecFile}".
        Respuestas recolectadas hasta el momento: ${jsonStringify(state.currentProject.answers)}
        
        Pregunta del usuario: "${msg}"
        
        Responde como un arquitecto de software de forma concisa, recomendando cómo rellenar esta sección o respondiendo a su duda técnica.
        `;
        
        // Para no crear endpoints extras, simulamos o usamos una ruta genérica de gemini. 
        // Hagamos que sea respondido de forma genérica o llamemos a un endpoint que evalúe texto libre.
        // Agreguemos en app.py un endpoint POST /api/copilot si es necesario, pero podemos consultarlo con una llamada limpia.
        // Hagamos que consulte al backend en una ruta limpia. Vamos a agregar en app.py un endpoint para el copiloto si es necesario, o reutilizar next-questions.
        // Modifiquemos app.py para añadir el endpoint de chat /api/copilot en breve, o usemos una llamada simple.
        // Por ahora, llamemos a un endpoint '/api/copilot' que crearemos en app.py para dar soporte real y potente.
        
        const copilotResp = await fetch('/api/copilot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({
                prompt: msg,
                activeFile: state.activeSpecFile,
                projectData: state.currentProject
            })
        });
        
        const copilotData = await copilotResp.json();
        
        loaderMsgEl.innerHTML = `<p>${copilotData.reply}</p>`;
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
    } catch (e) {
        console.error(e);
        loaderMsgEl.innerHTML = `<p style="color:var(--danger)">Hubo un error al procesar el mensaje con el Copiloto de IA.</p>`;
    }
}

function jsonStringify(obj) {
    try {
        return JSON.stringify(obj);
    } catch(e) {
        return '';
    }
}

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

// Alternar vista del editor (Respuestas vs Markdown)
function switchEditorView(viewName) {
    const editorTabs = document.querySelectorAll('.editor-tab');
    editorTabs.forEach(t => {
        if (t.dataset.view === viewName) {
            t.classList.add('active');
        } else {
            t.classList.remove('active');
        }
    });
    document.querySelectorAll('.editor-tab-content').forEach(c => c.classList.remove('active'));
    
    const viewEl = document.getElementById(`editor-view-${viewName}`);
    if (viewEl) viewEl.classList.add('active');
    
    if (viewName === 'markdown') {
        updateMarkdownPreview();
    }
}

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
    
    showPlanningState('loading-list');
    
    try {
        const response = await fetch('/api/plan-features', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Gemini-Key': state.apiKey
            },
            body: JSON.stringify({ project_data: state.currentProject })
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
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-primary btn-sm';
    closeBtn.style.marginTop = '16px';
    closeBtn.innerText = 'Cerrar y Ver en Workspace';
    closeBtn.addEventListener('click', () => {
        document.getElementById('planning-modal').classList.add('hidden');
        renderSpecTree();
    });
    logContainer.appendChild(closeBtn);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    renderSpecTree();
}
