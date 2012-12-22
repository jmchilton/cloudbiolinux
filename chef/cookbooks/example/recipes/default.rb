package "curl"

template "/etc/examle" do 
  source "example.erb"
  variables({
    :text => node[:example][:text],
    :data_dir => node[:cloudbiolinux_data_files]
  })
end