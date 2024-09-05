$(document).ready(function() {
    var isMenuOpen = false;
    const menu = $('#menu-agentes');
    const chat = $('.chat');
    chat.css('width', 'calc(100% - 0px)');
    $('#toggle-menu').on('click', function() {
        if (isMenuOpen) {
            menu.removeClass('open');
            $(this).text('Agentes');
            chat.css('width', 'calc(100% - 0px)');
        } else {
            menu.addClass('open');
            $(this).text('Cerrar Agentes');
            chat.css('width', 'calc(100% - 300px)');
        }
        isMenuOpen = !isMenuOpen;
    });

    var isMessageBeingSent = false;
    var currentAgentId = null;
    var lastFocusedElement;
    var respuestaRecibida = false;

    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    const modelosGroq = {
        'gemma2-9b-it': 'Gemma2 9B IT',
        'gemma-7b-it': 'Gemma 7B IT',
        'llama-3.1-70b-versatile': 'Llama 3.1 70B Versatile',
        'llama-3.1-8b-instant': 'Llama 3.1 8B Instant',
        'mixtral-8x7b-32768': 'Mixtral 8x7B 32768'
    };

    const modelosOpenAI = {
        'gpt-4o-mini': 'GPT-4O Mini',
        'gpt-3.5-turbo': 'GPT-3.5 Turbo',
        'gpt-4-turbo': 'GPT-4 Turbo'
    };

    function actualizarModelos(llm) {
        const modeloSelect = $('#modelo-select');
        modeloSelect.empty();
        let modelos = llm === 'groq' ? modelosGroq : modelosOpenAI;
        $.each(modelos, function(value, text) {
            modeloSelect.append($('<option></option>').val(value).text(text));
        });
    }

    function resetAgentStatus() {
        $('#agentes').find('.agente p').each(function() {
            $(this).text('Estado: Pendiente');
        });
    }

    socket.on('actualizar_estado', function(data) {
        if (data.progreso !== undefined) {
            $('#progress-bar').css('width', data.progreso + '%');
        }
        data.agentes.forEach(function(agente, index) {
            $('#estado-agente-' + (index + 1)).text('Estado: ' + escapeHtml(agente.estado));
        });
        if (data.respuesta_final && !respuestaRecibida) {
            $('#mensajes').append('<div class="mensaje-respuesta"><p>' + escapeHtml(data.respuesta_final).replace(/\n/g, '<br>') + '</p></div>');
            respuestaRecibida = true;
            $('#mensajes').scrollTop($('#mensajes')[0].scrollHeight);
        }
    });

    $('#mensaje').off('keypress').on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            $('#boton-enviar').click();
        }
    });

    $(document).off('click', '.agente').on('click', '.agente', function() {
        currentAgentId = $(this).data('agente-id');
        lastFocusedElement = $(this);
        $.get('/obtener_prompt', { agente_id: currentAgentId }, function(data) {
            $('#prompt-textarea').val(data.prompt);
            $('#modal-title').text('Editar Prompt del ' + $(lastFocusedElement).find('h3').text());
            
            
            $('#llm-select').val(data.llm);
            actualizarModelos(data.llm);  
            $('#modelo-select').val(data.modelo);  
            
            $('#promptModal').show();
            $('#prompt-textarea').focus();
        });
    });

    $('#guardar-prompt').off('click').on('click', function() {
        var nuevoPrompt = $('#prompt-textarea').val();
        var nuevoLLM = $('#llm-select').val();
        var nuevoModelo = $('#modelo-select').val();
        $.post('/guardar_prompt', { agente_id: currentAgentId, prompt: nuevoPrompt, llm: nuevoLLM, modelo: nuevoModelo }, function(data) {
            if (data.success) {
                $('#promptModal').hide();
                lastFocusedElement.focus();
            } else {
                alert('Error al guardar el prompt.');
            }
        });
    });

    $('#cancelar-prompt, .close').off('click').on('click', function() {
        $('#promptModal').hide();
        lastFocusedElement.focus();
    });

    $('#llm-select').on('change', function() {
        actualizarModelos($(this).val());
    });

    function escapeHtml(unsafe) {
        return unsafe.replace(/&/g, "&amp;")
                     .replace(/</g, "&lt;")
                     .replace(/>/g, "&gt;")
                     .replace(/"/g, "&quot;")
                     .replace(/'/g, "&#039;");
    }

    $('#boton-enviar').off('click').on('click', function() {
        if (isMessageBeingSent) {
            return;
        }

        var mensaje = $('#mensaje').val().trim();

        if (mensaje) {
            isMessageBeingSent = true;
            respuestaRecibida = false;
            resetAgentStatus();
            $('#boton-enviar').prop('disabled', true);
            $('#mensaje').prop('disabled', true);
            $('#progress-bar').css('width', '0%');
            $('#progress-container').show();
            $('#mensajes').append('<div class="mensaje-usuario"><p>' + escapeHtml(mensaje) + '</p></div>');
            $('#mensajes').scrollTop($('#mensajes')[0].scrollHeight);

            $.post('/enviar', { mensaje: mensaje }, function(datos) {
                $('#mensajes').scrollTop($('#mensajes')[0].scrollHeight);
                if (datos.respuesta_final && !respuestaRecibida) {
                    $('#mensajes').append('<div class="mensaje-respuesta"><p>' + escapeHtml(datos.respuesta_final).replace(/\n/g, '<br>') + '</p></div>');
                    respuestaRecibida = true;
                }
                datos.agentes.forEach(function(agente, index) {
                    $('#estado-agente-' + (index + 1)).text('Estado: ' + escapeHtml(agente.estado));
                });

                $('#boton-enviar').prop('disabled', false);
                $('#mensaje').prop('disabled', false).val('').focus();
                $('#progress-container').hide();
                isMessageBeingSent = false;
                $('#mensajes').scrollTop($('#mensajes')[0].scrollHeight);
            }).fail(function(xhr, status, error) {
                $('#debug-messages').text('Error al enviar la solicitud: ' + error).show();
                $('#boton-enviar').prop('disabled', false);
                $('#mensaje').prop('disabled', false).focus();
                isMessageBeingSent = false;
            });
        }
    });
});
