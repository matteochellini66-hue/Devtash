document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', async () => {
            // Trova l'elemento <code> che si trova nello stesso blocco del pulsante
            const codeBlock = button.parentElement.querySelector('code');
            const codeText = codeBlock.textContent;

            try {
                await navigator.clipboard.writeText(codeText);
                
                const originalText = button.textContent;
                button.textContent = 'Copiato!';

                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Impossibile copiare il testo: ', err);
            }
        });
    });
});
function create_page(){
    fetch("/create_page")
}