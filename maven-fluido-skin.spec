Name:		maven-fluido-skin
Version:	2.1.0
Release:	1
Summary:	Apache Maven Fluido site skin
Group:		Development/Java
License:	Apache-2.0
URL:		https://maven.apache.org/skins/maven-fluido-skin/
Source0:	https://github.com/apache/maven-fluido-skin/archive/refs/tags/maven-fluido-skin-%{version}.tar.gz#/maven-fluido-skin-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Maven site skin based on Bootstrap. The CSS and JavaScript bundles are
concatenated here because the Closure-based minify plugin is not
packaged. Velocity templates still filter the skin version.

%prep
%autosetup -n maven-fluido-skin-maven-fluido-skin-%{version}
rm -rf src/it .github
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

version = "%{version}"
rootdir = Path("src/main/resources")
css_names = [
    "bootstrap-2.3.2.css",
    "bootstrap-2.3.2-responsive.css",
    "maven-base.css",
    "maven-theme.css",
    "prettify.css",
    "gh-fork-ribbon.css",
]
js_names = [
    "jquery-1.11.2.js",
    "bootstrap-2.3.2.js",
    "prettify.js",
    "fluido.js",
    "anchor-4.3.1.js",
]

def cat(folder, names, destname):
    srcdir = rootdir / folder
    chunks = []
    for name in names:
        path = srcdir / name
        if not path.is_file():
            raise SystemExit("missing " + str(path))
        chunks.append("/* " + name + " */\n")
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        chunks.append("\n")
    (srcdir / destname).write_text("".join(chunks), encoding="utf-8")

cat("css", css_names, "apache-maven-fluido-" + version + ".min.css")
cat("js", js_names, "apache-maven-fluido-" + version + ".min.js")

tree = ET.parse("pom.xml")
root = tree.getroot()
parent = root.find(tag("parent"))
if parent is not None:
    root.remove(parent)
if root.find(tag("groupId")) is None:
    gid = ET.Element(tag("groupId"))
    gid.text = "org.apache.maven.skins"
    idx = 0
    for i, child in enumerate(list(root)):
        if child.tag == tag("modelVersion"):
            idx = i + 1
            break
    root.insert(idx, gid)
for profiles in list(root.findall(tag("profiles"))):
    root.remove(profiles)
build = root.find(tag("build"))
plugin_mgmt = build.find(tag("pluginManagement"))
if plugin_mgmt is not None:
    build.remove(plugin_mgmt)
plugins = build.find(tag("plugins"))
for plugin in list(plugins.findall(tag("plugin"))):
    if plugin.findtext(tag("artifactId")) == "minify-maven-plugin":
        plugins.remove(plugin)
resources = build.find(tag("resources"))
for resource in list(resources.findall(tag("resource"))):
    directory = resource.findtext(tag("directory")) or ""
    if "project.build.directory" in directory:
        resources.remove(resource)
resource = ET.SubElement(resources, tag("resource"))
add(resource, "directory", "${basedir}/src/main/resources")
includes = ET.SubElement(resource, tag("includes"))
for name in (
    "css/apache-maven-fluido-${project.version}.min.css",
    "js/apache-maven-fluido-${project.version}.min.js",
):
    add(includes, "include", name)
tree.write("pom.xml", encoding="utf-8", xml_declaration=True)
PY

%files -f .mfiles
%doc LICENSE NOTICE README.md
