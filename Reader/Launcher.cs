using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;
using System.Reflection;
[assembly: AssemblyTitle("Vayrshemon Reader")]
[assembly: AssemblyProduct("Vayrshemon Reader")]
[assembly: AssemblyVersion("1.0.0.0")]
internal static class Launcher {
    private static string Quote(string value) {
        var result=new StringBuilder("\""); int slashes=0;
        foreach(char c in value) {
            if(c=='\\') { slashes++; continue; }
            if(c=='"') { result.Append('\\',slashes*2+1);result.Append(c); }
            else { result.Append('\\',slashes);result.Append(c); }
            slashes=0;
        }
        result.Append('\\',slashes*2);result.Append('"');return result.ToString();
    }
    [STAThread] private static void Main(string[] args) {
        try {
            string folder=AppDomain.CurrentDomain.BaseDirectory;
            string root=Path.GetFullPath(Path.Combine(folder,".."));
            var command=new StringBuilder(Quote(Path.Combine(folder,"launch.py")));
            foreach(string arg in args) command.Append(" ").Append(Quote(arg));
            Process.Start(new ProcessStartInfo(Path.Combine(root,".venv","Scripts","pythonw.exe"),command.ToString()) {
                WorkingDirectory=root,UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden
            });
        } catch(Exception error) { MessageBox.Show(error.Message+"\n\nRun Reader\\setup.bat to check the runtime.","Vayrshemon Reader",MessageBoxButtons.OK,MessageBoxIcon.Error); }
    }
}
