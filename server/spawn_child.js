const { spawn } = require('child_process');

// Declare the function with a name
function spawn_child(command) {
    const child = spawn(command, [], { detached: true, shell: true });

    // Pipe child's stdout to parent's stdout
    child.stdout.on('data', (data) => {
        process.stdout.write(data);
    });

    // Pipe child's stderr to parent's stderr
    child.stderr.on('data', (data) => {
        process.stderr.write(data);
    });

    return child.pid;
}

// Add the function to module exports
module.exports = {
    spawn_child
};
